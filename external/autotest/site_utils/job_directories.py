import abc
import datetime
import glob
import json
import logging
import os
import re
import shutil

import common
from autotest_lib.client.common_lib import time_utils
from autotest_lib.client.common_lib import utils
from autotest_lib.server.cros.dynamic_suite import constants
from autotest_lib.server.cros.dynamic_suite import frontend_wrappers

try:
    from chromite.lib import metrics
except ImportError:
    metrics = utils.metrics_mock


SPECIAL_TASK_PATTERN = '.*/hosts/[^/]+/(\d+)-[^/]+'

def is_job_expired(age_limit, timestamp):
    """Check whether a job timestamp is older than an age limit.

  @param age_limit: Minimum age, measured in days.  If the value is
                    not positive, the job is always expired.
  @param timestamp: Timestamp of the job whose age we are checking.
                    The format must match time_utils.TIME_FMT.

  @returns True iff the job is old enough to be expired.
  """
    if age_limit <= 0:
        return True
    job_time = time_utils.time_string_to_datetime(timestamp)
    expiration = job_time + datetime.timedelta(days=age_limit)
    return datetime.datetime.now() >= expiration


def get_job_id_or_task_id(result_dir):
    """Extract job id or special task id from result_dir

    @param result_dir: path to the result dir.
            For test job:
            /usr/local/autotest/results/2032-chromeos-test/chromeos1-rack5-host6
            The hostname at the end is optional.
            For special task:
            /usr/local/autotest/results/hosts/chromeos1-rack5-host6/1343-cleanup

    @returns: str representing the job id or task id. Returns None if fail
        to parse job or task id from the result_dir.
    """
    if not result_dir:
        return
    result_dir = os.path.abspath(result_dir)
    # Result folder for job running inside container has only job id.
    ssp_job_pattern = '.*/(\d+)$'
    # Try to get the job ID from the last pattern of number-text. This avoids
    # issue with path like 123-results/456-debug_user, in which 456 is the real
    # job ID.
    m_job = re.findall('.*/(\d+)-[^/]+', result_dir)
    if m_job:
        return m_job[-1]
    m_special_task = re.match(SPECIAL_TASK_PATTERN, result_dir)
    if m_special_task:
        return m_special_task.group(1)
    m_ssp_job_pattern = re.match(ssp_job_pattern, result_dir)
    if m_ssp_job_pattern and utils.is_in_container():
        return m_ssp_job_pattern.group(1)
    return _get_swarming_run_id(result_dir)


def _get_swarming_run_id(path):
    """Extract the Swarming run_id for a Skylab task from the result path."""
    # Legacy swarming results are in directories like
    #   .../results/swarming-3e4391423c3a4311
    # In particular, the ending digit is never 0
    m_legacy_path = re.match('.*/swarming-([0-9a-fA-F]*[1-9a-fA-F])$', path)
    if m_legacy_path:
        return m_legacy_path.group(1)
    # New style swarming results are in directories like
    #   .../results/swarming-3e4391423c3a4310/1
    # - Results are one directory deeper.
    # - Ending digit of first directory is always 0.
    m_path = re.match('.*/swarming-([0-9a-fA-F]*)0/([1-9a-fA-F])$', path)
    if m_path:
        return m_path.group(1) + m_path.group(2)
    return None


class _JobDirectory(object):
    """State associated with a job to be offloaded.

  The full life-cycle of a job (including failure events that
  normally don't occur) looks like this:
   1. The job's results directory is discovered by
      `get_job_directories()`, and a job instance is created for it.
   2. Calls to `offload()` have no effect so long as the job
      isn't complete in the database and the job isn't expired
      according to the `age_limit` parameter.
   3. Eventually, the job is both finished and expired.  The next
      call to `offload()` makes the first attempt to offload the
      directory to GS.  Offload is attempted, but fails to complete
      (e.g. because of a GS problem).
   4. Finally, a call to `offload()` succeeds, and the directory no
      longer exists.  Now `is_offloaded()` is true, so the job
      instance is deleted, and future failures will not mention this
      directory any more.

  Only steps 1. and 4. are guaranteed to occur.  The others depend
  on the timing of calls to `offload()`, and on the reliability of
  the actual offload process.

  """

    __metaclass__ = abc.ABCMeta

    GLOB_PATTERN = None  # must be redefined in subclass

    def __init__(self, resultsdir):
        self.dirname = resultsdir
        self._id = get_job_id_or_task_id(resultsdir)
        self.offload_count = 0
        self.first_offload_start = 0

    @classmethod
    def get_job_directories(cls):
        """Return a list of directories of jobs that need offloading."""
        return [d for d in glob.glob(cls.GLOB_PATTERN) if os.path.isdir(d)]

    @abc.abstractmethod
    def get_timestamp_if_finished(self):
        """Return this job's timestamp from the database.

    If the database has not marked the job as finished, return
    `None`.  Otherwise, return a timestamp for the job.  The
    timestamp is to be used to determine expiration in
    `is_job_expired()`.

    @return Return `None` if the job is still running; otherwise
            return a string with a timestamp in the appropriate
            format.
    """
        raise NotImplementedError("_JobDirectory.get_timestamp_if_finished")

    def process_gs_instructions(self):
        """Process any gs_offloader instructions for this special task.

    @returns True/False if there is anything left to offload.
    """
        # Default support is to still offload the directory.
        return True


NO_OFFLOAD_README = """These results have been deleted rather than offloaded.
This is the expected behavior for passing jobs from the Commit Queue."""


class RegularJobDirectory(_JobDirectory):
    """Subclass of _JobDirectory for regular test jobs."""

    GLOB_PATTERN = '[0-9]*-*'

    def process_gs_instructions(self):
        """Process any gs_offloader instructions for this job.

    @returns True/False if there is anything left to offload.
    """
        # Go through the gs_offloader instructions file for each test in this job.
        for path in glob.glob(
                os.path.join(self.dirname, '*',
                             constants.GS_OFFLOADER_INSTRUCTIONS)):
            with open(path, 'r') as f:
                gs_off_instructions = json.load(f)
            if gs_off_instructions.get(constants.GS_OFFLOADER_NO_OFFLOAD):
                dirname = os.path.dirname(path)
                _remove_log_directory_contents(dirname)

        # Finally check if there's anything left to offload.
        if os.path.exists(self.dirname) and not os.listdir(self.dirname):
            shutil.rmtree(self.dirname)
            return False
        return True

    def get_timestamp_if_finished(self):
        """Get the timestamp to use for finished jobs.

    @returns the latest hqe finished_on time. If the finished_on times are null
             returns the job's created_on time.
    """
        entry = _cached_afe().get_jobs(id=self._id, finished=True)
        if not entry:
            return None
        hqes = _cached_afe().get_host_queue_entries(finished_on__isnull=False,
                                                    job_id=self._id)
        if not hqes:
            return entry[0].created_on
        # While most Jobs have 1 HQE, some can have multiple, so check them all.
        return max([hqe.finished_on for hqe in hqes])


def _remove_log_directory_contents(dirpath):
    """Remove log directory contents.

    Leave a note explaining what has happened to the logs.

    @param dirpath: Path to log directory.
    """
    shutil.rmtree(dirpath)
    os.mkdir(dirpath)
    breadcrumb_name = os.path.join(dirpath, 'logs-removed-readme.txt')
    with open(breadcrumb_name, 'w') as f:
        f.write(NO_OFFLOAD_README)


class SpecialJobDirectory(_JobDirectory):
    """Subclass of _JobDirectory for special (per-host) jobs."""

    GLOB_PATTERN = 'hosts/*/[0-9]*-*'

    def __init__(self, resultsdir):
        super(SpecialJobDirectory, self).__init__(resultsdir)

    def get_timestamp_if_finished(self):
        entry = _cached_afe().get_special_tasks(id=self._id, is_complete=True)
        return entry[0].time_finished if entry else None


def _find_results_dir(dirname):
    subdirs = []
    for root, dirs, files in os.walk(dirname, topdown=True):
        for f in files:
            if f == _OFFLOAD_MARKER:
                subdirs.append(root)
    return subdirs


_OFFLOAD_MARKER = ".ready_for_offload"
_marker_parse_error_metric = metrics.Counter(
    'chromeos/autotest/gs_offloader/offload_marker_parse_errors',
    description='Errors parsing the offload marker file')


class SwarmingJobDirectory(_JobDirectory):
    """Subclass of _JobDirectory for Skylab swarming jobs."""

    @classmethod
    def get_job_directories(cls):
        """Return a list of directories of jobs that need offloading."""
        # Legacy swarming results are in directories like
        #   .../results/swarming-3e4391423c3a4311
        # In particular, the ending digit is never 0
        jobdirs = [
                d for d in glob.glob('swarming-[0-9a-f]*[1-9a-f]')
                if os.path.isdir(d)
        ]
        # New style swarming results are in directories like
        #   .../results/swarming-3e4391423c3a4310/1
        # - Results are one directory deeper.
        # - Ending digit of first directory is always 0.
        new_style_topdir = [
                d for d in glob.glob('swarming-[0-9a-f]*0') if os.path.isdir(d)
        ]
        # When there are multiple tests run in one test_runner build,
        # the results will be one level deeper with the test_id
        # as one further subdirectory.
        # Example: .../results/swarming-3e4391423c3a4310/1/test_id
        for topdir in new_style_topdir:
            for d in glob.glob('%s/[1-9a-f]*' % topdir):
                subdirs = _find_results_dir(d)
                jobdirs += subdirs

        return jobdirs

    def get_timestamp_if_finished(self):
        """Get the timestamp to use for finished jobs.

    @returns the latest hqe finished_on time. If the finished_on times are null
             returns the job's created_on time.
    """
        marker_path = os.path.join(self.dirname, _OFFLOAD_MARKER)
        try:
            with open(marker_path) as f:
                ts_string = f.read().strip()
        except:
            return None
        try:
            ts = int(ts_string)
            return time_utils.epoch_time_to_date_string(ts)
        except ValueError as e:
            logging.debug('Error parsing %s for %s: %s', _OFFLOAD_MARKER,
                          self.dirname, e)
            _marker_parse_error_metric.increment()
            return None


_AFE = None
def _cached_afe():
    global _AFE
    if _AFE is None:
        _AFE = frontend_wrappers.RetryingAFE()
    return _AFE

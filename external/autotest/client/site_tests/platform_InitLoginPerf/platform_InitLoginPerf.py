# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import re
import shutil
import time

from autotest_lib.client.bin import test, utils
from autotest_lib.client.cros import cryptohome
from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib.cros import chrome

RE_ATTESTATION = 'Prepared successfully \((\d+)ms\)'
BOOT_TIMES_CMD = 'bootstat_summary'
BOOT_TIMES_DUMP_NAME = 'bootstat_summary'

def is_attestation_prepared():
    """Checks if attestation is prepared on the device.

    @return: Attestation readiness status - True/False.

    """
    return cryptohome.get_tpm_attestation_status().get(
            'prepared_for_enrollment', False)


def get_bootstat_timestamp(name, occurrence):
    """Gets the timestamp in ms of the given timestamp name and occurrence

    bootstat_summary output contains multiple lines. The first line are headers,
    and the rest are stats for event occurrences, one occurrence per line.

    @param name: Name of the timestamp.
    @param occurrence: Defines which occurrence of the timestamp should
                       be returned. The occurrence number is 1-based, and -1
                       means the latest occurrence.

    @return: Timestamp in ms or -1.0 if the requested occurrence doesn't exist.
    """
    try:
        output = utils.system_output('bootstat_summary %s' % name).splitlines()
        stats = float(output[occurrence].split()[0])
    except Exception:
        stats = -1.0

    return stats

def uptime_from_timestamp(name, occurrence=-1):
    """Extract the uptime in seconds for the captured timestamp.

    @param name: Name of the timestamp.
    @param occurrence: Defines which occurrence of the timestamp should
                       be returned. The occurrence number is 1-based.
                       Useful if it can be recorded multiple times.
                       Default: use the last one (-1).
    @raises error.TestFail: Raised if the requested timestamp doesn't exist.

    @return: Uptime in seconds.

    """
    timestamp = utils.wait_for_value(
        lambda: get_bootstat_timestamp(name, occurrence),
        max_threshold=0.001,
        timeout_sec=10)

    if timestamp < 0:
        raise error.TestFail('Failed to get timestamp for %s at occurrence %d.'
                             % (name, occurrence))

    return timestamp / 1000

def diff_timestamp(start, end):
    """Return the time difference between the two timestamps in seconds.
       Takes the last occurrence of each timestamp if multiple are available.

    @param start: The earlier timestamp.
    @param end: The later timestamp.

    @return: Difference in seconds.

    """
    return uptime_from_timestamp(end) - uptime_from_timestamp(start)

def get_duration(pattern, line):
    """Extract duration reported in syslog line.

    @param pattern: Regular expression, 1st group of which contains the
                    duration in ms.
    @param liner: Line from syslog.

    @return: Duration in seconds.

    """
    m = re.search(pattern, line)
    if not m:
        raise error.TestFail('Cannot get duration from %r', line)
    return float(m.group(1)) / 1000

class platform_InitLoginPerf(test.test):
    """Test to exercise and gather perf data for initialization and login."""

    version = 1

    def shall_init(self):
        """Check if this test shall perform and measure initialization.

        @return: True if yes, False otherwise.

        """
        return self.perform_init

    def save_file(self, name):
        """Save a single file to the results directory of the test.

        @param name: Name of the file.

        """
        shutil.copy(name, self.resultsdir)

    def save_cmd_output(self, cmd, name):
        """Save output of a command to the results directory of the test.

        @param cmd: Command to run.
        @param name: Name of the file to save to.

        """
        utils.system('%s > %s/%s' % (cmd, self.resultsdir, name))

    def wait_for_file(self, name, timeout=120):
        """Wait until a file is created.

           @param name: File name.
           @param timeout: Timeout waiting for the file.
           @raises error.TestFail: Raised in case of timeout.

        """
        if not utils.wait_for_value(lambda: os.path.isfile(name),
                                    expected_value=True,
                                    timeout_sec=timeout):
            raise error.TestFail('Timeout waiting for %r' % name)

    def wait_for_cryptohome_readiness(self):
        """Wait until cryptohome has started and initialized system salt."""
        self.wait_for_file('/home/.shadow/salt')

    def run_pre_login(self):
        """Run pre-login steps.
           1) Wait for cryptohome readiness (salt created).
           2) Trigger initialization (take ownership), if requested.
           3) Perform a pre-login delay, if requested.

           @param timeout: Timeout waiting for cryptohome first start.
           @raises error.TestFail: Raised in case of timeout.

        """
        self.wait_for_cryptohome_readiness()
        if self.shall_init():
            time.sleep(self.pre_init_delay)
            cryptohome.take_tpm_ownership(wait_for_ownership=False)

    def get_login_duration(self):
        """Extract login duration from recorded timestamps."""
        self.results['login-duration'] = diff_timestamp('login-prompt-visible',
                                                        'login-success')

    def wait_for_attestation_prepared(self, timeout=120):
        """Wait until attestation is prepared, i.e.
           AttestationPrepareForEnrollment init stage is done.

           @param timeout: Timeout waiting for attestation to be
                           prepared.
           @raises error.TestFail: Raised in case of timeout.

        """
        if not utils.wait_for_value(is_attestation_prepared,
                                    expected_value=True,
                                    timeout_sec=timeout):
            logging.debug('tpm_more_status: %r',
                          cryptohome.get_tpm_attestation_status())
            raise error.TestFail('Timeout waiting for attestation_prepared')

    def get_init_durations(self):
        """Extract init stage durations from syslog.

           @raises error.TestFail: Raised if duration lines were not found in
                                   syslog.

        """
        # Grep syslog for AttestationReady line
        attestation_line = ''
        with open('/var/log/messages', 'r') as syslog:
            for ln in syslog:
                if 'Attestation: Prepared successfully' in ln:
                    attestation_line = ln
        logging.debug('Attestation prepared: %r', attestation_line)
        if (not attestation_line):
            raise error.TestFail('Could not find duration lines in syslog')

        self.results['attestation-duration'] = get_duration(RE_ATTESTATION,
                                                            attestation_line)

    def run_post_login(self):
        """Run post-login steps.
           If initialization shall be performed: wait for attestation readiness
           and extract durations of initialization stages from syslog.
        """
        self.get_login_duration()
        self.save_cmd_output(BOOT_TIMES_CMD, BOOT_TIMES_DUMP_NAME)
        if self.shall_init():
            self.wait_for_attestation_prepared()
            self.get_init_durations()

    def run_once(self, perform_init=False, pre_init_delay=0):
        """Run the test.

        @param perform_init: Specifies if initialization shall be performed
                             to measure first boot performance.
        @param pre_init_delay: Delay before starting initialization.

        """
        self.perform_init = perform_init
        self.pre_init_delay = pre_init_delay
        self.results = {}

        self.run_pre_login()
        with chrome.Chrome(auto_login=True):
            self.run_post_login()

        logging.info('Results: %s', self.results)
        self.write_perf_keyval(self.results)

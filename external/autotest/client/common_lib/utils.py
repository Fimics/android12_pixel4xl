# Lint as: python2, python3
# Copyright (c) 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Convenience functions for use by tests or whomever.

There's no really good way to do this, as this isn't a class we can do
inheritance with, just a collection of static methods.
"""

# pylint: disable=missing-docstring

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import datetime
import errno
import inspect
import itertools
import logging
import os
import pickle
import random
import re
import resource
import select
import shutil
import signal
import socket
import six
from six.moves import input
from six.moves import range
from six.moves import urllib
from six.moves import zip
from six.moves import zip_longest
import six.moves.urllib.parse
import string
import struct
import subprocess
import textwrap
import threading
import time
import six.moves.queue
import uuid
import warnings

try:
    import hashlib
except ImportError as e:
    if six.PY2:
        import md5
        import sha
    else:
        raise ImportError("Broken hashlib imports %s", e)

import common

from autotest_lib.client.common_lib import env
from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib import global_config
from autotest_lib.client.common_lib import logging_manager
from autotest_lib.client.common_lib import metrics_mock_class
from autotest_lib.client.cros import constants

# pylint: disable=wildcard-import
from autotest_lib.client.common_lib.lsbrelease_utils import *


def deprecated(func):
    """This is a decorator which can be used to mark functions as deprecated.
    It will result in a warning being emmitted when the function is used."""
    def new_func(*args, **dargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **dargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


class _NullStream(object):
    def write(self, data):
        pass


    def flush(self):
        pass


TEE_TO_LOGS = object()
_the_null_stream = _NullStream()

DEVNULL = object()

DEFAULT_STDOUT_LEVEL = logging.DEBUG
DEFAULT_STDERR_LEVEL = logging.ERROR

# prefixes for logging stdout/stderr of commands
STDOUT_PREFIX = '[stdout] '
STDERR_PREFIX = '[stderr] '

# safe characters for the shell (do not need quoting)
_SHELL_QUOTING_ALLOWLIST = frozenset(string.ascii_letters +
                                    string.digits +
                                    '_-+=>|')

def custom_warning_handler(message, category, filename, lineno, file=None,
                           line=None):
    """Custom handler to log at the WARNING error level. Ignores |file|."""
    logging.warning(warnings.formatwarning(message, category, filename, lineno,
                                           line))

warnings.showwarning = custom_warning_handler

def get_stream_tee_file(stream, level, prefix=''):
    if stream is None:
        return _the_null_stream
    if stream is DEVNULL:
        return None
    if stream is TEE_TO_LOGS:
        return logging_manager.LoggingFile(level=level, prefix=prefix)
    return stream


def _join_with_nickname(base_string, nickname):
    if nickname:
        return '%s BgJob "%s" ' % (base_string, nickname)
    return base_string


# TODO: Cleanup and possibly eliminate |unjoinable|, which is only used in our
# ssh connection process, while fixing underlying
# semantics problem in BgJob. See crbug.com/279312
class BgJob(object):
    def __init__(self, command, stdout_tee=None, stderr_tee=None, verbose=True,
                 stdin=None, stdout_level=DEFAULT_STDOUT_LEVEL,
                 stderr_level=DEFAULT_STDERR_LEVEL, nickname=None,
                 unjoinable=False, env=None, extra_paths=None):
        """Create and start a new BgJob.

        This constructor creates a new BgJob, and uses Popen to start a new
        subprocess with given command. It returns without blocking on execution
        of the subprocess.

        After starting a new BgJob, use output_prepare to connect the process's
        stdout and stderr pipes to the stream of your choice.

        When the job is running, the jobs's output streams are only read from
        when process_output is called.

        @param command: command to be executed in new subprocess. May be either
                        a list, or a string (in which case Popen will be called
                        with shell=True)
        @param stdout_tee: (Optional) a file like object, TEE_TO_LOGS or
                           DEVNULL.
                           If not given, after finishing the process, the
                           stdout data from subprocess is available in
                           result.stdout.
                           If a file like object is given, in process_output(),
                           the stdout data from the subprocess will be handled
                           by the given file like object.
                           If TEE_TO_LOGS is given, in process_output(), the
                           stdout data from the subprocess will be handled by
                           the standard logging_manager.
                           If DEVNULL is given, the stdout of the subprocess
                           will be just discarded. In addition, even after
                           cleanup(), result.stdout will be just an empty
                           string (unlike the case where stdout_tee is not
                           given).
        @param stderr_tee: Same as stdout_tee, but for stderr.
        @param verbose: Boolean, make BgJob logging more verbose.
        @param stdin: Stream object, will be passed to Popen as the new
                      process's stdin.
        @param stdout_level: A logging level value. If stdout_tee was set to
                             TEE_TO_LOGS, sets the level that tee'd
                             stdout output will be logged at. Ignored
                             otherwise.
        @param stderr_level: Same as stdout_level, but for stderr.
        @param nickname: Optional string, to be included in logging messages
        @param unjoinable: Optional bool, default False.
                           This should be True for BgJobs running in background
                           and will never be joined with join_bg_jobs(), such
                           as the ssh connection. Instead, it is
                           caller's responsibility to terminate the subprocess
                           correctly, e.g. by calling nuke_subprocess().
                           This will lead that, calling join_bg_jobs(),
                           process_output() or cleanup() will result in an
                           InvalidBgJobCall exception.
                           Also, |stdout_tee| and |stderr_tee| must be set to
                           DEVNULL, otherwise InvalidBgJobCall is raised.
        @param env: Dict containing environment variables used in subprocess.
        @param extra_paths: Optional string list, to be prepended to the PATH
                            env variable in env (or os.environ dict if env is
                            not specified).
        """
        self.command = command
        self.unjoinable = unjoinable
        if (unjoinable and (stdout_tee != DEVNULL or stderr_tee != DEVNULL)):
            raise error.InvalidBgJobCall(
                'stdout_tee and stderr_tee must be DEVNULL for '
                'unjoinable BgJob')
        self._stdout_tee = get_stream_tee_file(
                stdout_tee, stdout_level,
                prefix=_join_with_nickname(STDOUT_PREFIX, nickname))
        self._stderr_tee = get_stream_tee_file(
                stderr_tee, stderr_level,
                prefix=_join_with_nickname(STDERR_PREFIX, nickname))
        self.result = CmdResult(command)

        # allow for easy stdin input by string, we'll let subprocess create
        # a pipe for stdin input and we'll write to it in the wait loop
        if isinstance(stdin, six.string_types):
            self.string_stdin = stdin
            stdin = subprocess.PIPE
        else:
            self.string_stdin = None

        # Prepend extra_paths to env['PATH'] if necessary.
        if extra_paths:
            env = (os.environ if env is None else env).copy()
            oldpath = env.get('PATH')
            env['PATH'] = os.pathsep.join(
                    extra_paths + ([oldpath] if oldpath else []))

        if verbose:
            logging.debug("Running '%s'", command)

        if type(command) == list:
            shell = False
            executable = None
        else:
            shell = True
            executable = '/bin/bash'

        with open('/dev/null', 'w') as devnull:
            # TODO b/169678884. close_fds was reverted to False, as there is a
            # large performance hit due to a docker + python2 bug. Eventually
            # update (everything) to python3. Moving this call to subprocess32
            # is also an option, but will require new packages to the drone/lxc
            # containers.

            self.sp = subprocess.Popen(
                command,
                stdin=stdin,
                stdout=devnull if stdout_tee == DEVNULL else subprocess.PIPE,
                stderr=devnull if stderr_tee == DEVNULL else subprocess.PIPE,
                preexec_fn=self._reset_sigpipe,
                shell=shell, executable=executable,
                env=env, close_fds=False)
        self._cleanup_called = False
        self._stdout_file = (
            None if stdout_tee == DEVNULL else six.StringIO())
        self._stderr_file = (
            None if stderr_tee == DEVNULL else six.StringIO())

    def process_output(self, stdout=True, final_read=False):
        """Read from process's output stream, and write data to destinations.

        This function reads up to 1024 bytes from the background job's
        stdout or stderr stream, and writes the resulting data to the BgJob's
        output tee and to the stream set up in output_prepare.

        Warning: Calls to process_output will block on reads from the
        subprocess stream, and will block on writes to the configured
        destination stream.

        @param stdout: True = read and process data from job's stdout.
                       False = from stderr.
                       Default: True
        @param final_read: Do not read only 1024 bytes from stream. Instead,
                           read and process all data until end of the stream.

        """
        if self.unjoinable:
            raise error.InvalidBgJobCall('Cannot call process_output on '
                                         'a job with unjoinable BgJob')
        if stdout:
            pipe, buf, tee = (
                self.sp.stdout, self._stdout_file, self._stdout_tee)
        else:
            pipe, buf, tee = (
                self.sp.stderr, self._stderr_file, self._stderr_tee)

        if not pipe:
            return

        if final_read:
            # read in all the data we can from pipe and then stop
            data = []
            while select.select([pipe], [], [], 0)[0]:
                data.append(self._read_data(pipe))
                if len(data[-1]) == 0:
                    break
            data = "".join(data)
        else:
            # perform a single read
            data = self._read_data(pipe)
        buf.write(data)
        tee.write(data)

    def _read_data(self, pipe):
        """Read & return the data from the provided pipe.

        Handles the changes to pipe reading & iostring writing in python 2/3.
        In python2 the buffer (iostring) can take bytes, where in python3 it
        must be a string. Formatting bytes to string in python 2 vs 3 seems
        to be a bit different. In 3, .decode() is needed, however in 2 that
        results in unicode (not str), breaking downstream users.

        """

        data = os.read(pipe.fileno(), 1024)
        if isinstance(data, bytes) and six.PY3:
            return data.decode()
        return data

    def cleanup(self):
        """Clean up after BgJob.

        Flush the stdout_tee and stderr_tee buffers, close the
        subprocess stdout and stderr buffers, and saves data from
        the configured stdout and stderr destination streams to
        self.result. Duplicate calls ignored with a warning.
        """
        if self.unjoinable:
            raise error.InvalidBgJobCall('Cannot call cleanup on '
                                         'a job with a unjoinable BgJob')
        if self._cleanup_called:
            logging.warning('BgJob [%s] received a duplicate call to '
                            'cleanup. Ignoring.', self.command)
            return
        try:
            if self.sp.stdout:
                self._stdout_tee.flush()
                self.sp.stdout.close()
                self.result.stdout = self._stdout_file.getvalue()

            if self.sp.stderr:
                self._stderr_tee.flush()
                self.sp.stderr.close()
                self.result.stderr = self._stderr_file.getvalue()
        finally:
            self._cleanup_called = True

    def _reset_sigpipe(self):
        if not env.IN_MOD_WSGI:
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def ip_to_long(ip):
    # !L is a long in network byte order
    return struct.unpack('!L', socket.inet_aton(ip))[0]


def long_to_ip(number):
    # See above comment.
    return socket.inet_ntoa(struct.pack('!L', number))


def create_subnet_mask(bits):
    return (1 << 32) - (1 << 32-bits)


def format_ip_with_mask(ip, mask_bits):
    masked_ip = ip_to_long(ip) & create_subnet_mask(mask_bits)
    return "%s/%s" % (long_to_ip(masked_ip), mask_bits)


def normalize_hostname(alias):
    ip = socket.gethostbyname(alias)
    return socket.gethostbyaddr(ip)[0]


def get_ip_local_port_range():
    match = re.match(r'\s*(\d+)\s*(\d+)\s*$',
                     read_one_line('/proc/sys/net/ipv4/ip_local_port_range'))
    return (int(match.group(1)), int(match.group(2)))


def set_ip_local_port_range(lower, upper):
    write_one_line('/proc/sys/net/ipv4/ip_local_port_range',
                   '%d %d\n' % (lower, upper))


def read_one_line(filename):
    f = open(filename, 'r')
    try:
        return f.readline().rstrip('\n')
    finally:
        f.close()


def read_file(filename):
    f = open(filename)
    try:
        return f.read()
    finally:
        f.close()


def get_field(data, param, linestart="", sep=" "):
    """
    Parse data from string.
    @param data: Data to parse.
        example:
          data:
             cpu   324 345 34  5 345
             cpu0  34  11  34 34  33
             ^^^^
             start of line
             params 0   1   2  3   4
    @param param: Position of parameter after linestart marker.
    @param linestart: String to which start line with parameters.
    @param sep: Separator between parameters regular expression.
    """
    search = re.compile(r"(?<=^%s)\s*(.*)" % linestart, re.MULTILINE)
    find = search.search(data)
    if find != None:
        return re.split("%s" % sep, find.group(1))[param]
    else:
        print("There is no line which starts with %s in data." % linestart)
        return None


def write_one_line(filename, line):
    open_write_close(filename, str(line).rstrip('\n') + '\n')


def open_write_close(filename, data):
    f = open(filename, 'w')
    try:
        f.write(data)
    finally:
        f.close()


def locate_file(path, base_dir=None):
    """Locates a file.

    @param path: The path of the file being located. Could be absolute or
        relative path. For relative path, it tries to locate the file from
        base_dir.

    @param base_dir (optional): Base directory of the relative path.

    @returns Absolute path of the file if found. None if path is None.
    @raises error.TestFail if the file is not found.
    """
    if path is None:
        return None

    if not os.path.isabs(path) and base_dir is not None:
        # Assume the relative path is based in autotest directory.
        path = os.path.join(base_dir, path)
    if not os.path.isfile(path):
        raise error.TestFail('ERROR: Unable to find %s' % path)
    return path


def matrix_to_string(matrix, header=None):
    """
    Return a pretty, aligned string representation of a nxm matrix.

    This representation can be used to print any tabular data, such as
    database results. It works by scanning the lengths of each element
    in each column, and determining the format string dynamically.

    @param matrix: Matrix representation (list with n rows of m elements).
    @param header: Optional tuple or list with header elements to be displayed.
    """
    if type(header) is list:
        header = tuple(header)
    lengths = []
    if header:
        for column in header:
            lengths.append(len(column))
    for row in matrix:
        for i, column in enumerate(row):
            column = six.ensure_binary(six.text_type(column), "utf-8")
            cl = len(column)
            try:
                ml = lengths[i]
                if cl > ml:
                    lengths[i] = cl
            except IndexError:
                lengths.append(cl)

    lengths = tuple(lengths)
    format_string = ""
    for length in lengths:
        format_string += "%-" + str(length) + "s "
    format_string += "\n"

    matrix_str = ""
    if header:
        matrix_str += format_string % header
    for row in matrix:
        matrix_str += format_string % tuple(row)

    return matrix_str


def read_keyval(path, type_tag=None):
    """
    Read a key-value pair format file into a dictionary, and return it.
    Takes either a filename or directory name as input. If it's a
    directory name, we assume you want the file to be called keyval.

    @param path: Full path of the file to read from.
    @param type_tag: If not None, only keyvals with key ending
                     in a suffix {type_tag} will be collected.
    """
    if os.path.isdir(path):
        path = os.path.join(path, 'keyval')
    if not os.path.exists(path):
        return {}

    if type_tag:
        pattern = r'^([-\.\w]+)\{%s\}=(.*)$' % type_tag
    else:
        pattern = r'^([-\.\w]+)=(.*)$'

    keyval = {}
    f = open(path)
    for line in f:
        line = re.sub('#.*', '', line).rstrip()
        if not line:
            continue
        match = re.match(pattern, line)
        if match:
            key = match.group(1)
            value = match.group(2)
            if re.search('^\d+$', value):
                value = int(value)
            elif re.search('^(\d+\.)?\d+$', value):
                value = float(value)
            keyval[key] = value
        else:
            raise ValueError('Invalid format line: %s' % line)
    f.close()
    return keyval


def write_keyval(path, dictionary, type_tag=None):
    """
    Write a key-value pair format file out to a file. This uses append
    mode to open the file, so existing text will not be overwritten or
    reparsed.

    If type_tag is None, then the key must be composed of alphanumeric
    characters (or dashes+underscores). However, if type-tag is not
    null then the keys must also have "{type_tag}" as a suffix. At
    the moment the only valid values of type_tag are "attr" and "perf".

    @param path: full path of the file to be written
    @param dictionary: the items to write
    @param type_tag: see text above
    """
    if os.path.isdir(path):
        path = os.path.join(path, 'keyval')
    keyval = open(path, 'a')

    if type_tag is None:
        key_regex = re.compile(r'^[-\.\w]+$')
    else:
        if type_tag not in ('attr', 'perf'):
            raise ValueError('Invalid type tag: %s' % type_tag)
        escaped_tag = re.escape(type_tag)
        key_regex = re.compile(r'^[-\.\w]+\{%s\}$' % escaped_tag)
    try:
        for key in sorted(dictionary.keys()):
            if not key_regex.search(key):
                raise ValueError('Invalid key: %s' % key)
            keyval.write('%s=%s\n' % (key, dictionary[key]))
    finally:
        keyval.close()


def is_url(path):
    """Return true if path looks like a URL"""
    # for now, just handle http and ftp
    url_parts = six.moves.urllib.parse.urlparse(path)
    return (url_parts[0] in ('http', 'ftp'))


def urlopen(url, data=None, timeout=5):
    """Wrapper to urllib2.urlopen with timeout addition."""

    # Save old timeout
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        return urllib.request.urlopen(url, data=data)
    finally:
        socket.setdefaulttimeout(old_timeout)


def urlretrieve(url, filename, data=None, timeout=300):
    """Retrieve a file from given url."""
    logging.debug('Fetching %s -> %s', url, filename)

    src_file = urlopen(url, data=data, timeout=timeout)
    try:
        dest_file = open(filename, 'wb')
        try:
            shutil.copyfileobj(src_file, dest_file)
        finally:
            dest_file.close()
    finally:
        src_file.close()


def hash(hashtype, input=None):
    """
    Returns an hash object of type md5 or sha1. This function is implemented in
    order to encapsulate hash objects in a way that is compatible with python
    2.4 and python 2.6 without warnings.

    Note that even though python 2.6 hashlib supports hash types other than
    md5 and sha1, we are artificially limiting the input values in order to
    make the function to behave exactly the same among both python
    implementations.

    @param input: Optional input string that will be used to update the hash.
    """
    # pylint: disable=redefined-builtin
    if hashtype not in ['md5', 'sha1']:
        raise ValueError("Unsupported hash type: %s" % hashtype)

    try:
        computed_hash = hashlib.new(hashtype)
    except NameError:
        if hashtype == 'md5':
            computed_hash = md5.new()
        elif hashtype == 'sha1':
            computed_hash = sha.new()

    if input:
        try:
            computed_hash.update(input.encode())
        except UnicodeError:
            computed_hash.update(input)


    return computed_hash


def get_file(src, dest, permissions=None):
    """Get a file from src, which can be local or a remote URL"""
    if src == dest:
        return

    if is_url(src):
        urlretrieve(src, dest)
    else:
        shutil.copyfile(src, dest)

    if permissions:
        os.chmod(dest, permissions)
    return dest


def unmap_url(srcdir, src, destdir='.'):
    """
    Receives either a path to a local file or a URL.
    returns either the path to the local file, or the fetched URL

    unmap_url('/usr/src', 'foo.tar', '/tmp')
                            = '/usr/src/foo.tar'
    unmap_url('/usr/src', 'http://site/file', '/tmp')
                            = '/tmp/file'
                            (after retrieving it)
    """
    if is_url(src):
        url_parts = six.moves.urllib.parse.urlparse(src)
        filename = os.path.basename(url_parts[2])
        dest = os.path.join(destdir, filename)
        return get_file(src, dest)
    else:
        return os.path.join(srcdir, src)


def update_version(srcdir, preserve_srcdir, new_version, install,
                   *args, **dargs):
    """
    Make sure srcdir is version new_version

    If not, delete it and install() the new version.

    In the preserve_srcdir case, we just check it's up to date,
    and if not, we rerun install, without removing srcdir
    """
    versionfile = os.path.join(srcdir, '.version')
    install_needed = True

    if os.path.exists(versionfile):
        old_version = pickle.load(open(versionfile))
        if old_version == new_version:
            install_needed = False

    if install_needed:
        if not preserve_srcdir and os.path.exists(srcdir):
            shutil.rmtree(srcdir)
        install(*args, **dargs)
        if os.path.exists(srcdir):
            pickle.dump(new_version, open(versionfile, 'w'))


def get_stderr_level(stderr_is_expected, stdout_level=DEFAULT_STDOUT_LEVEL):
    if stderr_is_expected:
        return stdout_level
    return DEFAULT_STDERR_LEVEL


def run(command, timeout=None, ignore_status=False, stdout_tee=None,
        stderr_tee=None, verbose=True, stdin=None, stderr_is_expected=None,
        stdout_level=None, stderr_level=None, args=(), nickname=None,
        ignore_timeout=False, env=None, extra_paths=None):
    """
    Run a command on the host.

    @param command: the command line string.
    @param timeout: time limit in seconds before attempting to kill the
            running process. The run() function will take a few seconds
            longer than 'timeout' to complete if it has to kill the process.
    @param ignore_status: do not raise an exception, no matter what the exit
            code of the command is.
    @param stdout_tee: optional file-like object to which stdout data
            will be written as it is generated (data will still be stored
            in result.stdout unless this is DEVNULL).
    @param stderr_tee: likewise for stderr.
    @param verbose: if True, log the command being run.
    @param stdin: stdin to pass to the executed process (can be a file
            descriptor, a file object of a real file or a string).
    @param stderr_is_expected: if True, stderr will be logged at the same level
            as stdout
    @param stdout_level: logging level used if stdout_tee is TEE_TO_LOGS;
            if None, a default is used.
    @param stderr_level: like stdout_level but for stderr.
    @param args: sequence of strings of arguments to be given to the command
            inside " quotes after they have been escaped for that; each
            element in the sequence will be given as a separate command
            argument
    @param nickname: Short string that will appear in logging messages
                     associated with this command.
    @param ignore_timeout: If True, timeouts are ignored otherwise if a
            timeout occurs it will raise CmdTimeoutError.
    @param env: Dict containing environment variables used in a subprocess.
    @param extra_paths: Optional string list, to be prepended to the PATH
                        env variable in env (or os.environ dict if env is
                        not specified).

    @return a CmdResult object or None if the command timed out and
            ignore_timeout is True
    @rtype: CmdResult

    @raise CmdError: the exit code of the command execution was not 0
    @raise CmdTimeoutError: the command timed out and ignore_timeout is False.
    """
    if isinstance(args, six.string_types):
        raise TypeError('Got a string for the "args" keyword argument, '
                        'need a sequence.')

    # In some cases, command will actually be a list
    # (For example, see get_user_hash in client/cros/cryptohome.py.)
    # So, to cover that case, detect if it's a string or not and convert it
    # into one if necessary.
    if not isinstance(command, six.string_types):
        command = ' '.join([sh_quote_word(arg) for arg in command])

    command = ' '.join([command] + [sh_quote_word(arg) for arg in args])

    if stderr_is_expected is None:
        stderr_is_expected = ignore_status
    if stdout_level is None:
        stdout_level = DEFAULT_STDOUT_LEVEL
    if stderr_level is None:
        stderr_level = get_stderr_level(stderr_is_expected, stdout_level)

    try:
        bg_job = join_bg_jobs(
            (BgJob(command, stdout_tee, stderr_tee, verbose, stdin=stdin,
                   stdout_level=stdout_level, stderr_level=stderr_level,
                   nickname=nickname, env=env, extra_paths=extra_paths),),
            timeout)[0]
    except error.CmdTimeoutError:
        if not ignore_timeout:
            raise
        return None

    if not ignore_status and bg_job.result.exit_status:
        raise error.CmdError(command, bg_job.result,
                             "Command returned non-zero exit status")

    return bg_job.result


def run_parallel(commands, timeout=None, ignore_status=False,
                 stdout_tee=None, stderr_tee=None,
                 nicknames=None):
    """
    Behaves the same as run() with the following exceptions:

    - commands is a list of commands to run in parallel.
    - ignore_status toggles whether or not an exception should be raised
      on any error.

    @return: a list of CmdResult objects
    """
    bg_jobs = []
    if nicknames is None:
        nicknames = []
    for (command, nickname) in zip_longest(commands, nicknames):
        bg_jobs.append(BgJob(command, stdout_tee, stderr_tee,
                             stderr_level=get_stderr_level(ignore_status),
                             nickname=nickname))

    # Updates objects in bg_jobs list with their process information
    join_bg_jobs(bg_jobs, timeout)

    for bg_job in bg_jobs:
        if not ignore_status and bg_job.result.exit_status:
            raise error.CmdError(command, bg_job.result,
                                 "Command returned non-zero exit status")

    return [bg_job.result for bg_job in bg_jobs]


@deprecated
def run_bg(command):
    """Function deprecated. Please use BgJob class instead."""
    bg_job = BgJob(command)
    return bg_job.sp, bg_job.result


def join_bg_jobs(bg_jobs, timeout=None):
    """Joins the bg_jobs with the current thread.

    Returns the same list of bg_jobs objects that was passed in.
    """
    if any(bg_job.unjoinable for bg_job in bg_jobs):
        raise error.InvalidBgJobCall(
                'join_bg_jobs cannot be called for unjoinable bg_job')

    timeout_error = False
    try:
        # We are holding ends to stdin, stdout pipes
        # hence we need to be sure to close those fds no mater what
        start_time = time.time()
        timeout_error = _wait_for_commands(bg_jobs, start_time, timeout)

        for bg_job in bg_jobs:
            # Process stdout and stderr
            bg_job.process_output(stdout=True,final_read=True)
            bg_job.process_output(stdout=False,final_read=True)
    finally:
        # close our ends of the pipes to the sp no matter what
        for bg_job in bg_jobs:
            bg_job.cleanup()

    if timeout_error:
        # TODO: This needs to be fixed to better represent what happens when
        # running in parallel. However this is backwards compatable, so it will
        # do for the time being.
        raise error.CmdTimeoutError(
                bg_jobs[0].command, bg_jobs[0].result,
                "Command(s) did not complete within %d seconds" % timeout)


    return bg_jobs


def _wait_for_commands(bg_jobs, start_time, timeout):
    """Waits for background jobs by select polling their stdout/stderr.

    @param bg_jobs: A list of background jobs to wait on.
    @param start_time: Time used to calculate the timeout lifetime of a job.
    @param timeout: The timeout of the list of bg_jobs.

    @return: True if the return was due to a timeout, False otherwise.
    """

    # To check for processes which terminate without producing any output
    # a 1 second timeout is used in select.
    SELECT_TIMEOUT = 1

    read_list = []
    write_list = []
    reverse_dict = {}

    for bg_job in bg_jobs:
        if bg_job.sp.stdout:
            read_list.append(bg_job.sp.stdout)
            reverse_dict[bg_job.sp.stdout] = (bg_job, True)
        if bg_job.sp.stderr:
            read_list.append(bg_job.sp.stderr)
            reverse_dict[bg_job.sp.stderr] = (bg_job, False)
        if bg_job.string_stdin is not None:
            write_list.append(bg_job.sp.stdin)
            reverse_dict[bg_job.sp.stdin] = bg_job

    if timeout:
        stop_time = start_time + timeout
        time_left = stop_time - time.time()
    else:
        time_left = None # so that select never times out

    while not timeout or time_left > 0:
        # select will return when we may write to stdin, when there is
        # stdout/stderr output we can read (including when it is
        # EOF, that is the process has terminated) or when a non-fatal
        # signal was sent to the process. In the last case the select returns
        # EINTR, and we continue waiting for the job if the signal handler for
        # the signal that interrupted the call allows us to.
        try:
            read_ready, write_ready, _ = select.select(read_list, write_list,
                                                       [], SELECT_TIMEOUT)
        except select.error as v:
            if v[0] == errno.EINTR:
                logging.warning(v)
                continue
            else:
                raise
        # os.read() has to be used instead of
        # subproc.stdout.read() which will otherwise block
        for file_obj in read_ready:
            bg_job, is_stdout = reverse_dict[file_obj]
            bg_job.process_output(is_stdout)

        for file_obj in write_ready:
            # we can write PIPE_BUF bytes without blocking
            # POSIX requires PIPE_BUF is >= 512
            bg_job = reverse_dict[file_obj]
            file_obj.write(bg_job.string_stdin[:512])
            bg_job.string_stdin = bg_job.string_stdin[512:]
            # no more input data, close stdin, remove it from the select set
            if not bg_job.string_stdin:
                file_obj.close()
                write_list.remove(file_obj)
                del reverse_dict[file_obj]

        all_jobs_finished = True
        for bg_job in bg_jobs:
            if bg_job.result.exit_status is not None:
                continue

            bg_job.result.exit_status = bg_job.sp.poll()
            if bg_job.result.exit_status is not None:
                # process exited, remove its stdout/stdin from the select set
                bg_job.result.duration = time.time() - start_time
                if bg_job.sp.stdout:
                    read_list.remove(bg_job.sp.stdout)
                    del reverse_dict[bg_job.sp.stdout]
                if bg_job.sp.stderr:
                    read_list.remove(bg_job.sp.stderr)
                    del reverse_dict[bg_job.sp.stderr]
            else:
                all_jobs_finished = False

        if all_jobs_finished:
            return False

        if timeout:
            time_left = stop_time - time.time()

    # Kill all processes which did not complete prior to timeout
    for bg_job in bg_jobs:
        if bg_job.result.exit_status is not None:
            continue

        logging.warning('run process timeout (%s) fired on: %s', timeout,
                        bg_job.command)
        if nuke_subprocess(bg_job.sp) is None:
            # If process could not be SIGKILL'd, log kernel stack.
            logging.warning(read_file('/proc/%d/stack' % bg_job.sp.pid))
        bg_job.result.exit_status = bg_job.sp.poll()
        bg_job.result.duration = time.time() - start_time

    return True


def pid_is_alive(pid):
    """
    True if process pid exists and is not yet stuck in Zombie state.
    Zombies are impossible to move between cgroups, etc.
    pid can be integer, or text of integer.
    """
    path = '/proc/%s/stat' % pid

    try:
        stat = read_one_line(path)
    except IOError:
        if not os.path.exists(path):
            # file went away
            return False
        raise

    return stat.split()[2] != 'Z'


def signal_pid(pid, sig):
    """
    Sends a signal to a process id. Returns True if the process terminated
    successfully, False otherwise.
    """
    try:
        os.kill(pid, sig)
    except OSError:
        # The process may have died before we could kill it.
        pass

    for _ in range(5):
        if not pid_is_alive(pid):
            return True
        time.sleep(1)

    # The process is still alive
    return False


def nuke_subprocess(subproc):
    # check if the subprocess is still alive, first
    if subproc.poll() is not None:
        return subproc.poll()

    # the process has not terminated within timeout,
    # kill it via an escalating series of signals.
    signal_queue = [signal.SIGTERM, signal.SIGKILL]
    for sig in signal_queue:
        signal_pid(subproc.pid, sig)
        if subproc.poll() is not None:
            return subproc.poll()


def nuke_pid(pid, signal_queue=(signal.SIGTERM, signal.SIGKILL)):
    # the process has not terminated within timeout,
    # kill it via an escalating series of signals.
    pid_path = '/proc/%d/'
    if not os.path.exists(pid_path % pid):
        # Assume that if the pid does not exist in proc it is already dead.
        logging.error('No listing in /proc for pid:%d.', pid)
        raise error.AutoservPidAlreadyDeadError('Could not kill nonexistant '
                                                'pid: %s.', pid)
    for sig in signal_queue:
        if signal_pid(pid, sig):
            return

    # no signal successfully terminated the process
    raise error.AutoservRunError('Could not kill %d for process name: %s' % (
            pid, get_process_name(pid)), None)


def system(command, timeout=None, ignore_status=False):
    """
    Run a command

    @param timeout: timeout in seconds
    @param ignore_status: if ignore_status=False, throw an exception if the
            command's exit code is non-zero
            if ignore_stauts=True, return the exit code.

    @return exit status of command
            (note, this will always be zero unless ignore_status=True)
    """
    return run(command, timeout=timeout, ignore_status=ignore_status,
               stdout_tee=TEE_TO_LOGS, stderr_tee=TEE_TO_LOGS).exit_status


def system_parallel(commands, timeout=None, ignore_status=False):
    """This function returns a list of exit statuses for the respective
    list of commands."""
    return [bg_jobs.exit_status for bg_jobs in
            run_parallel(commands, timeout=timeout, ignore_status=ignore_status,
                         stdout_tee=TEE_TO_LOGS, stderr_tee=TEE_TO_LOGS)]


def system_output(command, timeout=None, ignore_status=False,
                  retain_output=False, args=()):
    """
    Run a command and return the stdout output.

    @param command: command string to execute.
    @param timeout: time limit in seconds before attempting to kill the
            running process. The function will take a few seconds longer
            than 'timeout' to complete if it has to kill the process.
    @param ignore_status: do not raise an exception, no matter what the exit
            code of the command is.
    @param retain_output: set to True to make stdout/stderr of the command
            output to be also sent to the logging system
    @param args: sequence of strings of arguments to be given to the command
            inside " quotes after they have been escaped for that; each
            element in the sequence will be given as a separate command
            argument

    @return a string with the stdout output of the command.
    """
    if retain_output:
        out = run(command, timeout=timeout, ignore_status=ignore_status,
                  stdout_tee=TEE_TO_LOGS, stderr_tee=TEE_TO_LOGS,
                  args=args).stdout
    else:
        out = run(command, timeout=timeout, ignore_status=ignore_status,
                  args=args).stdout
    if out[-1:] == '\n':
        out = out[:-1]
    return out


def system_output_parallel(commands, timeout=None, ignore_status=False,
                           retain_output=False):
    if retain_output:
        out = [bg_job.stdout for bg_job
               in run_parallel(commands, timeout=timeout,
                               ignore_status=ignore_status,
                               stdout_tee=TEE_TO_LOGS, stderr_tee=TEE_TO_LOGS)]
    else:
        out = [bg_job.stdout for bg_job in run_parallel(commands,
                                  timeout=timeout, ignore_status=ignore_status)]
    for _ in out:
        if out[-1:] == '\n':
            out = out[:-1]
    return out


def strip_unicode(input_obj):
    if type(input_obj) == list:
        return [strip_unicode(i) for i in input_obj]
    elif type(input_obj) == dict:
        output = {}
        for key in input_obj.keys():
            output[str(key)] = strip_unicode(input_obj[key])
        return output
    elif type(input_obj) == six.text_type:
        return str(input_obj)
    else:
        return input_obj


def get_cpu_percentage(function, *args, **dargs):
    """Returns a tuple containing the CPU% and return value from function call.

    This function calculates the usage time by taking the difference of
    the user and system times both before and after the function call.
    """
    child_pre = resource.getrusage(resource.RUSAGE_CHILDREN)
    self_pre = resource.getrusage(resource.RUSAGE_SELF)
    start = time.time()
    to_return = function(*args, **dargs)
    elapsed = time.time() - start
    self_post = resource.getrusage(resource.RUSAGE_SELF)
    child_post = resource.getrusage(resource.RUSAGE_CHILDREN)

    # Calculate CPU Percentage
    s_user, s_system = [a - b for a, b in zip(self_post, self_pre)[:2]]
    c_user, c_system = [a - b for a, b in zip(child_post, child_pre)[:2]]
    cpu_percent = (s_user + c_user + s_system + c_system) / elapsed

    return cpu_percent, to_return


def get_arch(run_function=run):
    """
    Get the hardware architecture of the machine.
    If specified, run_function should return a CmdResult object and throw a
    CmdError exception.
    If run_function is anything other than utils.run(), it is used to
    execute the commands. By default (when set to utils.run()) this will
    just examine os.uname()[4].
    """

    # Short circuit from the common case.
    if run_function == run:
        return re.sub(r'i\d86$', 'i386', os.uname()[4])

    # Otherwise, use the run_function in case it hits a remote machine.
    arch = run_function('/bin/uname -m').stdout.rstrip()
    if re.match(r'i\d86$', arch):
        arch = 'i386'
    return arch

def get_arch_userspace(run_function=run):
    """
    Get the architecture by userspace (possibly different from kernel).
    """
    archs = {
        'arm': 'ELF 32-bit.*, ARM,',
        'arm64': 'ELF 64-bit.*, ARM aarch64,',
        'i386': 'ELF 32-bit.*, Intel 80386,',
        'x86_64': 'ELF 64-bit.*, x86-64,',
    }

    cmd = 'file --brief --dereference /bin/sh'
    filestr = run_function(cmd).stdout.rstrip()
    for a, regex in six.iteritems(archs):
        if re.match(regex, filestr):
            return a

    return get_arch()


def get_num_logical_cpus_per_socket(run_function=run):
    """
    Get the number of cores (including hyperthreading) per cpu.
    run_function is used to execute the commands. It defaults to
    utils.run() but a custom method (if provided) should be of the
    same schema as utils.run. It should return a CmdResult object and
    throw a CmdError exception.
    """
    siblings = run_function('grep "^siblings" /proc/cpuinfo').stdout.rstrip()
    num_siblings = [int(x) for x in
                    re.findall(r'^siblings\s*:\s*(\d+)\s*$', siblings, re.M)]
    if len(num_siblings) == 0:
        raise error.TestError('Unable to find siblings info in /proc/cpuinfo')
    if min(num_siblings) != max(num_siblings):
        raise error.TestError('Number of siblings differ %r' %
                              num_siblings)
    return num_siblings[0]


def set_high_performance_mode(host=None):
    """
    Sets the kernel governor mode to the highest setting.
    Returns previous governor state.
    """
    original_governors = get_scaling_governor_states(host)
    set_scaling_governors('performance', host)
    return original_governors


def set_scaling_governors(value, host=None):
    """
    Sets all scaling governor to string value.
    Sample values: 'performance', 'interactive', 'ondemand', 'powersave'.
    """
    paths = _get_cpufreq_paths('scaling_governor', host)
    if not paths:
        logging.info("Could not set governor states, as no files of the form "
                     "'/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor' "
                     "were found.")
    run_func = host.run if host else system
    for path in paths:
        cmd = 'echo %s > %s' % (value, path)
        logging.info('Writing scaling governor mode \'%s\' -> %s', value, path)
        # On Tegra CPUs can be dynamically enabled/disabled. Ignore failures.
        run_func(cmd, ignore_status=True)


def _get_cpufreq_paths(filename, host=None):
    """
    Returns a list of paths to the governors.
    """
    run_func = host.run if host else run
    glob = '/sys/devices/system/cpu/cpu*/cpufreq/' + filename
    # Simple glob expansion; note that CPUs may come and go, causing these
    # paths to change at any time.
    cmd = 'echo ' + glob
    try:
        paths = run_func(cmd, verbose=False).stdout.split()
    except error.CmdError:
        return []
    # If the glob result equals itself, then we likely didn't match any real
    # paths (assuming 'cpu*' is not a real path).
    if paths == [glob]:
        return []
    return paths


def get_scaling_governor_states(host=None):
    """
    Returns a list of (performance governor path, current state) tuples.
    """
    paths = _get_cpufreq_paths('scaling_governor', host)
    path_value_list = []
    run_func = host.run if host else run
    for path in paths:
        value = run_func('head -n 1 %s' % path, verbose=False).stdout
        path_value_list.append((path, value))
    return path_value_list


def restore_scaling_governor_states(path_value_list, host=None):
    """
    Restores governor states. Inverse operation to get_scaling_governor_states.
    """
    run_func = host.run if host else system
    for (path, value) in path_value_list:
        cmd = 'echo %s > %s' % (value.rstrip('\n'), path)
        # On Tegra CPUs can be dynamically enabled/disabled. Ignore failures.
        run_func(cmd, ignore_status=True)


def merge_trees(src, dest):
    """
    Merges a source directory tree at 'src' into a destination tree at
    'dest'. If a path is a file in both trees than the file in the source
    tree is APPENDED to the one in the destination tree. If a path is
    a directory in both trees then the directories are recursively merged
    with this function. In any other case, the function will skip the
    paths that cannot be merged (instead of failing).
    """
    if not os.path.exists(src):
        return # exists only in dest
    elif not os.path.exists(dest):
        if os.path.isfile(src):
            shutil.copy2(src, dest) # file only in src
        else:
            shutil.copytree(src, dest, symlinks=True) # dir only in src
        return
    elif os.path.isfile(src) and os.path.isfile(dest):
        # src & dest are files in both trees, append src to dest
        destfile = open(dest, "a")
        try:
            srcfile = open(src)
            try:
                destfile.write(srcfile.read())
            finally:
                srcfile.close()
        finally:
            destfile.close()
    elif os.path.isdir(src) and os.path.isdir(dest):
        # src & dest are directories in both trees, so recursively merge
        for name in os.listdir(src):
            merge_trees(os.path.join(src, name), os.path.join(dest, name))
    else:
        # src & dest both exist, but are incompatible
        return


class CmdResult(object):
    """
    Command execution result.

    command:     String containing the command line itself
    exit_status: Integer exit code of the process
    stdout:      String containing stdout of the process
    stderr:      String containing stderr of the process
    duration:    Elapsed wall clock time running the process
    """


    def __init__(self, command="", stdout="", stderr="",
                 exit_status=None, duration=0):
        self.command = command
        self.exit_status = exit_status
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration


    def __eq__(self, other):
        if type(self) == type(other):
            return (self.command == other.command
                    and self.exit_status == other.exit_status
                    and self.stdout == other.stdout
                    and self.stderr == other.stderr
                    and self.duration == other.duration)
        else:
            return NotImplemented


    def __repr__(self):
        wrapper = textwrap.TextWrapper(width = 78,
                                       initial_indent="\n    ",
                                       subsequent_indent="    ")

        stdout = self.stdout.rstrip()
        if stdout:
            stdout = "\nstdout:\n%s" % stdout

        stderr = self.stderr.rstrip()
        if stderr:
            stderr = "\nstderr:\n%s" % stderr

        return ("* Command: %s\n"
                "Exit status: %s\n"
                "Duration: %s\n"
                "%s"
                "%s"
                % (wrapper.fill(str(self.command)), self.exit_status,
                self.duration, stdout, stderr))


class run_randomly:
    def __init__(self, run_sequentially=False):
        # Run sequentially is for debugging control files
        self.test_list = []
        self.run_sequentially = run_sequentially


    def add(self, *args, **dargs):
        test = (args, dargs)
        self.test_list.append(test)


    def run(self, fn):
        while self.test_list:
            test_index = random.randint(0, len(self.test_list)-1)
            if self.run_sequentially:
                test_index = 0
            (args, dargs) = self.test_list.pop(test_index)
            fn(*args, **dargs)


def import_site_module(path, module, dummy=None, modulefile=None):
    """
    Try to import the site specific module if it exists.

    @param path full filename of the source file calling this (ie __file__)
    @param module full module name
    @param dummy dummy value to return in case there is no symbol to import
    @param modulefile module filename

    @return site specific module or dummy

    @raises ImportError if the site file exists but imports fails
    """
    short_module = module[module.rfind(".") + 1:]

    if not modulefile:
        modulefile = short_module + ".py"

    if os.path.exists(os.path.join(os.path.dirname(path), modulefile)):
        return __import__(module, {}, {}, [short_module])
    return dummy


def import_site_symbol(path, module, name, dummy=None, modulefile=None):
    """
    Try to import site specific symbol from site specific file if it exists

    @param path full filename of the source file calling this (ie __file__)
    @param module full module name
    @param name symbol name to be imported from the site file
    @param dummy dummy value to return in case there is no symbol to import
    @param modulefile module filename

    @return site specific symbol or dummy

    @raises ImportError if the site file exists but imports fails
    """
    module = import_site_module(path, module, modulefile=modulefile)
    if not module:
        return dummy

    # special unique value to tell us if the symbol can't be imported
    cant_import = object()

    obj = getattr(module, name, cant_import)
    if obj is cant_import:
        return dummy

    return obj


def import_site_class(path, module, classname, baseclass, modulefile=None):
    """
    Try to import site specific class from site specific file if it exists

    Args:
        path: full filename of the source file calling this (ie __file__)
        module: full module name
        classname: class name to be loaded from site file
        baseclass: base class object to return when no site file present or
            to mixin when site class exists but is not inherited from baseclass
        modulefile: module filename

    Returns: baseclass if site specific class does not exist, the site specific
        class if it exists and is inherited from baseclass or a mixin of the
        site specific class and baseclass when the site specific class exists
        and is not inherited from baseclass

    Raises: ImportError if the site file exists but imports fails
    """

    res = import_site_symbol(path, module, classname, None, modulefile)
    if res:
        if not issubclass(res, baseclass):
            # if not a subclass of baseclass then mix in baseclass with the
            # site specific class object and return the result
            res = type(classname, (res, baseclass), {})
    else:
        res = baseclass

    return res


def import_site_function(path, module, funcname, dummy, modulefile=None):
    """
    Try to import site specific function from site specific file if it exists

    Args:
        path: full filename of the source file calling this (ie __file__)
        module: full module name
        funcname: function name to be imported from site file
        dummy: dummy function to return in case there is no function to import
        modulefile: module filename

    Returns: site specific function object or dummy

    Raises: ImportError if the site file exists but imports fails
    """

    return import_site_symbol(path, module, funcname, dummy, modulefile)


def _get_pid_path(program_name):
    my_path = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(my_path, "..", "..",
                                        "%s.pid" % program_name))


def write_pid(program_name):
    """
    Try to drop <program_name>.pid in the main autotest directory.

    Args:
      program_name: prefix for file name
    """
    pidfile = open(_get_pid_path(program_name), "w")
    try:
        pidfile.write("%s\n" % os.getpid())
    finally:
        pidfile.close()


def delete_pid_file_if_exists(program_name):
    """
    Tries to remove <program_name>.pid from the main autotest directory.
    """
    pidfile_path = _get_pid_path(program_name)

    try:
        os.remove(pidfile_path)
    except OSError:
        if not os.path.exists(pidfile_path):
            return
        raise


def get_pid_from_file(program_name):
    """
    Reads the pid from <program_name>.pid in the autotest directory.

    @param program_name the name of the program
    @return the pid if the file exists, None otherwise.
    """
    pidfile_path = _get_pid_path(program_name)
    if not os.path.exists(pidfile_path):
        return None

    pidfile = open(_get_pid_path(program_name), 'r')

    try:
        try:
            pid = int(pidfile.readline())
        except IOError:
            if not os.path.exists(pidfile_path):
                return None
            raise
    finally:
        pidfile.close()

    return pid


def get_process_name(pid):
    """
    Get process name from PID.
    @param pid: PID of process.
    @return: Process name if PID stat file exists or 'Dead PID' if it does not.
    """
    pid_stat_path = "/proc/%d/stat"
    if not os.path.exists(pid_stat_path % pid):
        return "Dead Pid"
    return get_field(read_file(pid_stat_path % pid), 1)[1:-1]


def program_is_alive(program_name):
    """
    Checks if the process is alive and not in Zombie state.

    @param program_name the name of the program
    @return True if still alive, False otherwise
    """
    pid = get_pid_from_file(program_name)
    if pid is None:
        return False
    return pid_is_alive(pid)


def signal_program(program_name, sig=signal.SIGTERM):
    """
    Sends a signal to the process listed in <program_name>.pid

    @param program_name the name of the program
    @param sig signal to send
    """
    pid = get_pid_from_file(program_name)
    if pid:
        signal_pid(pid, sig)


def get_relative_path(path, reference):
    """Given 2 absolute paths "path" and "reference", compute the path of
    "path" as relative to the directory "reference".

    @param path the absolute path to convert to a relative path
    @param reference an absolute directory path to which the relative
        path will be computed
    """
    # normalize the paths (remove double slashes, etc)
    assert(os.path.isabs(path))
    assert(os.path.isabs(reference))

    path = os.path.normpath(path)
    reference = os.path.normpath(reference)

    # we could use os.path.split() but it splits from the end
    path_list = path.split(os.path.sep)[1:]
    ref_list = reference.split(os.path.sep)[1:]

    # find the longest leading common path
    for i in range(min(len(path_list), len(ref_list))):
        if path_list[i] != ref_list[i]:
            # decrement i so when exiting this loop either by no match or by
            # end of range we are one step behind
            i -= 1
            break
    i += 1
    # drop the common part of the paths, not interested in that anymore
    del path_list[:i]

    # for each uncommon component in the reference prepend a ".."
    path_list[:0] = ['..'] * (len(ref_list) - i)

    return os.path.join(*path_list)


def sh_escape(command):
    """
    Escape special characters from a command so that it can be passed
    as a double quoted (" ") string in a (ba)sh command.

    Args:
            command: the command string to escape.

    Returns:
            The escaped command string. The required englobing double
            quotes are NOT added and so should be added at some point by
            the caller.

    See also: http://www.tldp.org/LDP/abs/html/escapingsection.html
    """
    command = command.replace("\\", "\\\\")
    command = command.replace("$", r'\$')
    command = command.replace('"', r'\"')
    command = command.replace('`', r'\`')
    return command


def sh_quote_word(text, allowlist=_SHELL_QUOTING_ALLOWLIST):
    r"""Quote a string to make it safe as a single word in a shell command.

    POSIX shell syntax recognizes no escape characters inside a single-quoted
    string.  So, single quotes can safely quote any string of characters except
    a string with a single quote character.  A single quote character must be
    quoted with the sequence '\'' which translates to:
        '  -> close current quote
        \' -> insert a literal single quote
        '  -> reopen quoting again.

    This is safe for all combinations of characters, including embedded and
    trailing backslashes in odd or even numbers.

    This is also safe for nesting, e.g. the following is a valid use:

        adb_command = 'adb shell %s' % (
                sh_quote_word('echo %s' % sh_quote_word('hello world')))

    @param text: The string to be quoted into a single word for the shell.
    @param allowlist: Optional list of characters that do not need quoting.
                      Defaults to a known good list of characters.

    @return A string, possibly quoted, safe as a single word for a shell.
    """
    if all(c in allowlist for c in text):
        return text
    return "'" + text.replace("'", r"'\''") + "'"


def configure(extra=None, configure='./configure'):
    """
    Run configure passing in the correct host, build, and target options.

    @param extra: extra command line arguments to pass to configure
    @param configure: which configure script to use
    """
    args = []
    if 'CHOST' in os.environ:
        args.append('--host=' + os.environ['CHOST'])
    if 'CBUILD' in os.environ:
        args.append('--build=' + os.environ['CBUILD'])
    if 'CTARGET' in os.environ:
        args.append('--target=' + os.environ['CTARGET'])
    if extra:
        args.append(extra)

    system('%s %s' % (configure, ' '.join(args)))


def make(extra='', make='make', timeout=None, ignore_status=False):
    """
    Run make, adding MAKEOPTS to the list of options.

    @param extra: extra command line arguments to pass to make.
    """
    cmd = '%s %s %s' % (make, os.environ.get('MAKEOPTS', ''), extra)
    return system(cmd, timeout=timeout, ignore_status=ignore_status)


def compare_versions(ver1, ver2):
    """Version number comparison between ver1 and ver2 strings.

    >>> compare_tuple("1", "2")
    -1
    >>> compare_tuple("foo-1.1", "foo-1.2")
    -1
    >>> compare_tuple("1.2", "1.2a")
    -1
    >>> compare_tuple("1.2b", "1.2a")
    1
    >>> compare_tuple("1.3.5.3a", "1.3.5.3b")
    -1

    Args:
        ver1: version string
        ver2: version string

    Returns:
        int:  1 if ver1 >  ver2
              0 if ver1 == ver2
             -1 if ver1 <  ver2
    """
    ax = re.split('[.-]', ver1)
    ay = re.split('[.-]', ver2)
    while len(ax) > 0 and len(ay) > 0:
        cx = ax.pop(0)
        cy = ay.pop(0)
        maxlen = max(len(cx), len(cy))
        c = cmp(cx.zfill(maxlen), cy.zfill(maxlen))
        if c != 0:
            return c
    return cmp(len(ax), len(ay))


def args_to_dict(args):
    """Convert autoserv extra arguments in the form of key=val or key:val to a
    dictionary.  Each argument key is converted to lowercase dictionary key.

    Args:
        args - list of autoserv extra arguments.

    Returns:
        dictionary
    """
    arg_re = re.compile(r'(\w+)[:=](.*)$')
    args_dict = {}
    for arg in args:
        match = arg_re.match(arg)
        if match:
            args_dict[match.group(1).lower()] = match.group(2)
        else:
            logging.warning("args_to_dict: argument '%s' doesn't match "
                            "'%s' pattern. Ignored.", arg, arg_re.pattern)
    return args_dict


def get_unused_port():
    """
    Finds a semi-random available port. A race condition is still
    possible after the port number is returned, if another process
    happens to bind it.

    Returns:
        A port number that is unused on both TCP and UDP.
    """

    def try_bind(port, socket_type, socket_proto):
        s = socket.socket(socket.AF_INET, socket_type, socket_proto)
        try:
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('', port))
                return s.getsockname()[1]
            except socket.error:
                return None
        finally:
            s.close()

    # On the 2.6 kernel, calling try_bind() on UDP socket returns the
    # same port over and over. So always try TCP first.
    while True:
        # Ask the OS for an unused port.
        port = try_bind(0, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        # Check if this port is unused on the other protocol.
        if port and try_bind(port, socket.SOCK_DGRAM, socket.IPPROTO_UDP):
            return port


def ask(question, auto=False):
    """
    Raw input with a prompt that emulates logging.

    @param question: Question to be asked
    @param auto: Whether to return "y" instead of asking the question
    """
    if auto:
        logging.info("%s (y/n) y", question)
        return "y"
    return input("%s INFO | %s (y/n) " %
                     (time.strftime("%H:%M:%S", time.localtime()), question))


def rdmsr(address, cpu=0):
    """
    Reads an x86 MSR from the specified CPU, returns as long integer.
    """
    with open('/dev/cpu/%s/msr' % cpu, 'r', 0) as fd:
        fd.seek(address)
        return struct.unpack('=Q', fd.read(8))[0]


def wait_for_value(func,
                   expected_value=None,
                   min_threshold=None,
                   max_threshold=None,
                   timeout_sec=10):
    """
    Returns the value of func().  If |expected_value|, |min_threshold|, and
    |max_threshold| are not set, returns immediately.

    If |expected_value| is set, polls the return value until |expected_value| is
    reached, and returns that value.

    If either |max_threshold| or |min_threshold| is set, this function will
    will repeatedly call func() until the return value reaches or exceeds one of
    these thresholds.

    Polling will stop after |timeout_sec| regardless of these thresholds.

    @param func: function whose return value is to be waited on.
    @param expected_value: wait for func to return this value.
    @param min_threshold: wait for func value to reach or fall below this value.
    @param max_threshold: wait for func value to reach or rise above this value.
    @param timeout_sec: Number of seconds to wait before giving up and
                        returning whatever value func() last returned.

    Return value:
        The most recent return value of func().
    """
    value = None
    start_time_sec = time.time()
    while True:
        value = func()
        if (expected_value is None and \
            min_threshold is None and \
            max_threshold is None) or \
           (expected_value is not None and value == expected_value) or \
           (min_threshold is not None and value <= min_threshold) or \
           (max_threshold is not None and value >= max_threshold):
            break

        if time.time() - start_time_sec >= timeout_sec:
            break
        time.sleep(0.1)

    return value


def wait_for_value_changed(func,
                           old_value=None,
                           timeout_sec=10):
    """
    Returns the value of func().

    The function polls the return value until it is different from |old_value|,
    and returns that value.

    Polling will stop after |timeout_sec|.

    @param func: function whose return value is to be waited on.
    @param old_value: wait for func to return a value different from this.
    @param timeout_sec: Number of seconds to wait before giving up and
                        returning whatever value func() last returned.

    @returns The most recent return value of func().
    """
    value = None
    start_time_sec = time.time()
    while True:
        value = func()
        if value != old_value:
            break

        if time.time() - start_time_sec >= timeout_sec:
            break
        time.sleep(0.1)

    return value


CONFIG = global_config.global_config

# Keep checking if the pid is alive every second until the timeout (in seconds)
CHECK_PID_IS_ALIVE_TIMEOUT = 6

_LOCAL_HOST_LIST = ('localhost', '127.0.0.1')

# The default address of a vm gateway.
DEFAULT_VM_GATEWAY = '10.0.2.2'

# Google Storage bucket URI to store results in.
DEFAULT_OFFLOAD_GSURI = CONFIG.get_config_value(
        'CROS', 'results_storage_server', default=None)

# Default Moblab Ethernet Interface.
_MOBLAB_ETH_0 = 'eth0'
_MOBLAB_ETH_1 = 'eth1'

# A list of subnets that requires dedicated devserver and drone in the same
# subnet. Each item is a tuple of (subnet_ip, mask_bits), e.g.,
# ('192.168.0.0', 24))
RESTRICTED_SUBNETS = []

def _setup_restricted_subnets():
    restricted_subnets_list = CONFIG.get_config_value(
            'CROS', 'restricted_subnets', type=list, default=[])
    # TODO(dshi): Remove the code to split subnet with `:` after R51 is
    # off stable channel, and update shadow config to use `/` as
    # delimiter for consistency.
    for subnet in restricted_subnets_list:
        ip, mask_bits = subnet.split('/') if '/' in subnet \
                        else subnet.split(':')
        RESTRICTED_SUBNETS.append((ip, int(mask_bits)))

_setup_restricted_subnets()

# regex pattern for CLIENT/wireless_ssid_ config. For example, global config
# can have following config in CLIENT section to indicate that hosts in subnet
# 192.168.0.1/24 should use wireless ssid of `ssid_1`
# wireless_ssid_192.168.0.1/24: ssid_1
WIRELESS_SSID_PATTERN = 'wireless_ssid_(.*)/(\d+)'


def get_moblab_serial_number():
    """Gets a unique identifier for the moblab.

    Serial number is the prefered identifier, use it if
    present, however fallback is the ethernet mac address.
    """
    for vpd_key in ['serial_number', 'ethernet_mac']:
      try:
          cmd_result = run('sudo vpd -g %s' % vpd_key)
          if cmd_result and cmd_result.stdout:
            return cmd_result.stdout
      except error.CmdError as e:
          logging.error(str(e))
          logging.info(vpd_key)
    return 'NoSerialNumber'


def ping(host,
         deadline=None,
         tries=None,
         timeout=60,
         ignore_timeout=False,
         user=None):
    """Attempt to ping |host|.

    Shell out to 'ping' if host is an IPv4 addres or 'ping6' if host is an
    IPv6 address to try to reach |host| for |timeout| seconds.
    Returns exit code of ping.

    Per 'man ping', if you specify BOTH |deadline| and |tries|, ping only
    returns 0 if we get responses to |tries| pings within |deadline| seconds.

    Specifying |deadline| or |count| alone should return 0 as long as
    some packets receive responses.

    Note that while this works with literal IPv6 addresses it will not work
    with hostnames that resolve to IPv6 only.

    @param host: the host to ping.
    @param deadline: seconds within which |tries| pings must succeed.
    @param tries: number of pings to send.
    @param timeout: number of seconds after which to kill 'ping' command.
    @param ignore_timeout: If true, timeouts won't raise CmdTimeoutError.
    @param user: Run as a specific user
    @return exit code of ping command.
    """
    args = [host]
    cmd = 'ping6' if re.search(r':.*:', host) else 'ping'

    if deadline:
        args.append('-w%d' % deadline)
    if tries:
        args.append('-c%d' % tries)

    if user != None:
        args = [user, '-c', ' '.join([cmd] + args)]
        cmd = 'su'

    result = run(cmd,
                 args=args,
                 verbose=True,
                 ignore_status=True,
                 timeout=timeout,
                 ignore_timeout=ignore_timeout,
                 stderr_tee=TEE_TO_LOGS)

    # Sometimes the ping process times out even though a deadline is set. If
    # ignore_timeout is set, it will fall through to here instead of raising.
    if result is None:
        logging.debug('Unusual ping result (timeout)')
        # From man ping: If a packet count and deadline are both specified, and
        # fewer than count packets are received by the time the deadline has
        # arrived, it will also exit with code 1. On other error it exits with
        # code 2.
        return 1 if deadline and tries else 2

    rc = result.exit_status
    lines = result.stdout.splitlines()

    # rc=0: host reachable
    # rc=1: host unreachable
    # other: an error (do not abbreviate)
    if rc in (0, 1):
        # Report the two stats lines, as a single line.
        # [-2]: packets transmitted, 1 received, 0% packet loss, time 0ms
        # [-1]: rtt min/avg/max/mdev = 0.497/0.497/0.497/0.000 ms
        stats = lines[-2:]
        while '' in stats:
            stats.remove('')

        if stats or len(lines) < 2:
            logging.debug('[rc=%s] %s', rc, '; '.join(stats))
        else:
            logging.debug('[rc=%s] Ping output:\n%s',
                          rc, result.stdout)
    else:
        output = result.stdout.rstrip()
        if output:
            logging.debug('Unusual ping result (rc=%s):\n%s', rc, output)
        else:
            logging.debug('Unusual ping result (rc=%s).', rc)
    return rc


def host_is_in_lab_zone(hostname):
    """Check if the host is in the CLIENT.dns_zone.

    @param hostname: The hostname to check.
    @returns True if hostname.dns_zone resolves, otherwise False.
    """
    host_parts = hostname.split('.')
    dns_zone = CONFIG.get_config_value('CLIENT', 'dns_zone', default=None)
    fqdn = '%s.%s' % (host_parts[0], dns_zone)
    logging.debug('Checking if host %s is in lab zone.', fqdn)
    try:
        socket.gethostbyname(fqdn)
        return True
    except socket.gaierror:
        return False


def host_is_in_power_lab(hostname):
    """Check if the hostname is in power lab.

    Example: chromeos1-power-host2.cros

    @param hostname: The hostname to check.
    @returns True if hostname match power lab hostname, otherwise False.
    """
    pattern = r'chromeos\d+-power-host\d+(\.cros(\.corp(\.google\.com)?)?)?$'
    return re.match(pattern, hostname) is not None


def get_power_lab_wlan_hostname(hostname):
    """Return wlan hostname for host in power lab.

    Example: chromeos1-power-host2.cros -> chromeos1-power-host2-wlan.cros

    @param hostname: The hostname in power lab.
    @returns wlan hostname.
    """
    split_host = hostname.split('.')
    split_host[0] += '-wlan'
    return '.'.join(split_host)


def in_moblab_ssp():
    """Detects if this execution is inside an SSP container on moblab."""
    config_is_moblab = CONFIG.get_config_value('SSP', 'is_moblab', type=bool,
                                               default=False)
    return is_in_container() and config_is_moblab


def get_chrome_version(job_views):
    """
    Retrieves the version of the chrome binary associated with a job.

    When a test runs we query the chrome binary for it's version and drop
    that value into a client keyval. To retrieve the chrome version we get all
    the views associated with a test from the db, including those of the
    server and client jobs, and parse the version out of the first test view
    that has it. If we never ran a single test in the suite the job_views
    dictionary will not contain a chrome version.

    This method cannot retrieve the chrome version from a dictionary that
    does not conform to the structure of an autotest tko view.

    @param job_views: a list of a job's result views, as returned by
                      the get_detailed_test_views method in rpc_interface.
    @return: The chrome version string, or None if one can't be found.
    """

    # Aborted jobs have no views.
    if not job_views:
        return None

    for view in job_views:
        if (view.get('attributes')
            and constants.CHROME_VERSION in list(view['attributes'].keys())):

            return view['attributes'].get(constants.CHROME_VERSION)

    logging.warning('Could not find chrome version for failure.')
    return None


def get_moblab_id():
    """Gets the moblab random id.

    The random id file is cached on disk. If it does not exist, a new file is
    created the first time.

    @returns the moblab random id.
    """
    moblab_id_filepath = '/home/moblab/.moblab_id'
    try:
        if os.path.exists(moblab_id_filepath):
            with open(moblab_id_filepath, 'r') as moblab_id_file:
                random_id = moblab_id_file.read()
        else:
            random_id = uuid.uuid1().hex
            with open(moblab_id_filepath, 'w') as moblab_id_file:
                moblab_id_file.write('%s' % random_id)
    except IOError as e:
        # Possible race condition, another process has created the file.
        # Sleep a second to make sure the file gets closed.
        logging.info(e)
        time.sleep(1)
        with open(moblab_id_filepath, 'r') as moblab_id_file:
            random_id = moblab_id_file.read()
    return random_id


def get_offload_gsuri():
    """Return the GSURI to offload test results to.

    For the normal use case this is the results_storage_server in the
    global_config.

    However partners using Moblab will be offloading their results to a
    subdirectory of their image storage buckets. The subdirectory is
    determined by the MAC Address of the Moblab device.

    @returns gsuri to offload test results to.
    """
    # For non-moblab, use results_storage_server or default.
    if not is_moblab():  # pylint: disable=undefined-variable
        return DEFAULT_OFFLOAD_GSURI

    # For moblab, use results_storage_server or image_storage_server as bucket
    # name and mac-address/moblab_id as path.
    gsuri = DEFAULT_OFFLOAD_GSURI
    if not gsuri:
        gsuri = "%sresults/" % CONFIG.get_config_value('CROS',
                                                       'image_storage_server')

    return '%s%s/%s/' % (gsuri, get_moblab_serial_number(), get_moblab_id())


# TODO(petermayo): crosbug.com/31826 Share this with _GsUpload in
# //chromite.git/buildbot/prebuilt.py somewhere/somehow
def gs_upload(local_file, remote_file, acl, result_dir=None,
              transfer_timeout=300, acl_timeout=300):
    """Upload to GS bucket.

    @param local_file: Local file to upload
    @param remote_file: Remote location to upload the local_file to.
    @param acl: name or file used for controlling access to the uploaded
                file.
    @param result_dir: Result directory if you want to add tracing to the
                       upload.
    @param transfer_timeout: Timeout for this upload call.
    @param acl_timeout: Timeout for the acl call needed to confirm that
                        the uploader has permissions to execute the upload.

    @raise CmdError: the exit code of the gsutil call was not 0.

    @returns True/False - depending on if the upload succeeded or failed.
    """
    # https://developers.google.com/storage/docs/accesscontrol#extension
    CANNED_ACLS = ['project-private', 'private', 'public-read',
                   'public-read-write', 'authenticated-read',
                   'bucket-owner-read', 'bucket-owner-full-control']
    _GSUTIL_BIN = 'gsutil'
    acl_cmd = None
    if acl in CANNED_ACLS:
        cmd = '%s cp -a %s %s %s' % (_GSUTIL_BIN, acl, local_file, remote_file)
    else:
        # For private uploads we assume that the overlay board is set up
        # properly and a googlestore_acl.xml is present, if not this script
        # errors
        cmd = '%s cp -a private %s %s' % (_GSUTIL_BIN, local_file, remote_file)
        if not os.path.exists(acl):
            logging.error('Unable to find ACL File %s.', acl)
            return False
        acl_cmd = '%s setacl %s %s' % (_GSUTIL_BIN, acl, remote_file)
    if not result_dir:
        run(cmd, timeout=transfer_timeout, verbose=True)
        if acl_cmd:
            run(acl_cmd, timeout=acl_timeout, verbose=True)
        return True
    with open(os.path.join(result_dir, 'tracing'), 'w') as ftrace:
        ftrace.write('Preamble\n')
        run(cmd, timeout=transfer_timeout, verbose=True,
                       stdout_tee=ftrace, stderr_tee=ftrace)
        if acl_cmd:
            ftrace.write('\nACL setting\n')
            # Apply the passed in ACL xml file to the uploaded object.
            run(acl_cmd, timeout=acl_timeout, verbose=True,
                           stdout_tee=ftrace, stderr_tee=ftrace)
        ftrace.write('Postamble\n')
        return True


def gs_ls(uri_pattern):
    """Returns a list of URIs that match a given pattern.

    @param uri_pattern: a GS URI pattern, may contain wildcards

    @return A list of URIs matching the given pattern.

    @raise CmdError: the gsutil command failed.

    """
    gs_cmd = ' '.join(['gsutil', 'ls', uri_pattern])
    result = system_output(gs_cmd).splitlines()
    return [path.rstrip() for path in result if path]


def nuke_pids(pid_list, signal_queue=None):
    """
    Given a list of pid's, kill them via an esclating series of signals.

    @param pid_list: List of PID's to kill.
    @param signal_queue: Queue of signals to send the PID's to terminate them.

    @return: A mapping of the signal name to the number of processes it
        was sent to.
    """
    if signal_queue is None:
        signal_queue = [signal.SIGTERM, signal.SIGKILL]
    sig_count = {}
    # Though this is slightly hacky it beats hardcoding names anyday.
    sig_names = dict((k, v) for v, k in six.iteritems(signal.__dict__)
                     if v.startswith('SIG'))
    for sig in signal_queue:
        logging.debug('Sending signal %s to the following pids:', sig)
        sig_count[sig_names.get(sig, 'unknown_signal')] = len(pid_list)
        for pid in pid_list:
            logging.debug('Pid %d', pid)
            try:
                os.kill(pid, sig)
            except OSError:
                # The process may have died from a previous signal before we
                # could kill it.
                pass
        if sig == signal.SIGKILL:
            return sig_count
        pid_list = [pid for pid in pid_list if pid_is_alive(pid)]
        if not pid_list:
            break
        time.sleep(CHECK_PID_IS_ALIVE_TIMEOUT)
    failed_list = []
    for pid in pid_list:
        if pid_is_alive(pid):
            failed_list.append('Could not kill %d for process name: %s.' % pid,
                               get_process_name(pid))
    if failed_list:
        raise error.AutoservRunError('Following errors occured: %s' %
                                     failed_list, None)
    return sig_count


def externalize_host(host):
    """Returns an externally accessible host name.

    @param host: a host name or address (string)

    @return An externally visible host name or address

    """
    return socket.gethostname() if host in _LOCAL_HOST_LIST else host


def urlopen_socket_timeout(url, data=None, timeout=5):
    """
    Wrapper to urllib2.urlopen with a socket timeout.

    This method will convert all socket timeouts to
    TimeoutExceptions, so we can use it in conjunction
    with the rpc retry decorator and continue to handle
    other URLErrors as we see fit.

    @param url: The url to open.
    @param data: The data to send to the url (eg: the urlencoded dictionary
                 used with a POST call).
    @param timeout: The timeout for this urlopen call.

    @return: The response of the urlopen call.

    @raises: error.TimeoutException when a socket timeout occurs.
             urllib2.URLError for errors that not caused by timeout.
             urllib2.HTTPError for errors like 404 url not found.
    """
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        return urllib.request.urlopen(url, data=data)
    except urllib.error.URLError as e:
        if type(e.reason) is socket.timeout:
            raise error.TimeoutException(str(e))
        raise
    finally:
        socket.setdefaulttimeout(old_timeout)


def parse_chrome_version(version_string):
    """
    Parse a chrome version string and return version and milestone.

    Given a chrome version of the form "W.X.Y.Z", return "W.X.Y.Z" as
    the version and "W" as the milestone.

    @param version_string: Chrome version string.
    @return: a tuple (chrome_version, milestone). If the incoming version
             string is not of the form "W.X.Y.Z", chrome_version will
             be set to the incoming "version_string" argument and the
             milestone will be set to the empty string.
    """
    match = re.search('(\d+)\.\d+\.\d+\.\d+', version_string)
    ver = match.group(0) if match else version_string
    milestone = match.group(1) if match else ''
    return ver, milestone


def parse_gs_uri_version(uri):
    """Pull out major.minor.sub from image URI

    @param uri: A GS URI for a bucket containing ChromeOS build artifacts
    @return: The build version as a string in the form 'major.minor.sub'

    """
    return re.sub('.*(R[0-9]+|LATEST)-', '', uri).strip('/')


def compare_gs_uri_build_versions(x, y):
    """Compares two bucket URIs by their version string

    @param x: A GS URI for a bucket containing ChromeOS build artifacts
    @param y: Another GS URI for a bucket containing ChromeOS build artifacts
    @return: 1 if x > y, -1 if x < y, and 0 if x == y

    """
    # Converts a gs uri 'gs://.../R75-<major>.<minor>.<sub>' to
    # [major, minor, sub]
    split_version = lambda v: [int(x) for x in
                               parse_gs_uri_version(v).split('.')]

    x_version = split_version(x)
    y_version = split_version(y)

    for a, b in zip(x_version, y_version):
        if a > b:
            return 1
        elif b > a:
            return -1

    return 0


def is_localhost(server):
    """Check if server is equivalent to localhost.

    @param server: Name of the server to check.

    @return: True if given server is equivalent to localhost.

    @raise socket.gaierror: If server name failed to be resolved.
    """
    if server in _LOCAL_HOST_LIST:
        return True
    try:
        return (socket.gethostbyname(socket.gethostname()) ==
                socket.gethostbyname(server))
    except socket.gaierror:
        logging.error('Failed to resolve server name %s.', server)
        return False


def get_function_arg_value(func, arg_name, args, kwargs):
    """Get the value of the given argument for the function.

    @param func: Function being called with given arguments.
    @param arg_name: Name of the argument to look for value.
    @param args: arguments for function to be called.
    @param kwargs: keyword arguments for function to be called.

    @return: The value of the given argument for the function.

    @raise ValueError: If the argument is not listed function arguemnts.
    @raise KeyError: If no value is found for the given argument.
    """
    if arg_name in kwargs:
        return kwargs[arg_name]

    argspec = inspect.getargspec(func)
    index = argspec.args.index(arg_name)
    try:
        return args[index]
    except IndexError:
        try:
            # The argument can use a default value. Reverse the default value
            # so argument with default value can be counted from the last to
            # the first.
            return argspec.defaults[::-1][len(argspec.args) - index - 1]
        except IndexError:
            raise KeyError('Argument %s is not given a value. argspec: %s, '
                           'args:%s, kwargs:%s' %
                           (arg_name, argspec, args, kwargs))


def has_systemd():
    """Check if the host is running systemd.

    @return: True if the host uses systemd, otherwise returns False.
    """
    return os.path.basename(os.readlink('/proc/1/exe')) == 'systemd'


def get_real_user():
    """Get the real user that runs the script.

    The function check environment variable SUDO_USER for the user if the
    script is run with sudo. Otherwise, it returns the value of environment
    variable USER.

    @return: The user name that runs the script.

    """
    user = os.environ.get('SUDO_USER')
    if not user:
        user = os.environ.get('USER')
    return user


def get_service_pid(service_name):
    """Return pid of service.

    @param service_name: string name of service.

    @return: pid or 0 if service is not running.
    """
    if has_systemd():
        # systemctl show prints 'MainPID=0' if the service is not running.
        cmd_result = run('systemctl show -p MainPID %s' %
                                    service_name, ignore_status=True)
        return int(cmd_result.stdout.split('=')[1])
    else:
        cmd_result = run('status %s' % service_name,
                                        ignore_status=True)
        if 'start/running' in cmd_result.stdout:
            return int(cmd_result.stdout.split()[3])
        return 0


def control_service(service_name, action='start', ignore_status=True):
    """Controls a service. It can be used to start, stop or restart
    a service.

    @param service_name: string service to be restarted.

    @param action: string choice of action to control command.

    @param ignore_status: boolean ignore if system command fails.

    @return: status code of the executed command.
    """
    if action not in ('start', 'stop', 'restart'):
        raise ValueError('Unknown action supplied as parameter.')

    control_cmd = action + ' ' + service_name
    if has_systemd():
        control_cmd = 'systemctl ' + control_cmd
    return system(control_cmd, ignore_status=ignore_status)


def restart_service(service_name, ignore_status=True):
    """Restarts a service

    @param service_name: string service to be restarted.

    @param ignore_status: boolean ignore if system command fails.

    @return: status code of the executed command.
    """
    return control_service(service_name, action='restart',
                           ignore_status=ignore_status)


def start_service(service_name, ignore_status=True):
    """Starts a service

    @param service_name: string service to be started.

    @param ignore_status: boolean ignore if system command fails.

    @return: status code of the executed command.
    """
    return control_service(service_name, action='start',
                           ignore_status=ignore_status)


def stop_service(service_name, ignore_status=True):
    """Stops a service

    @param service_name: string service to be stopped.

    @param ignore_status: boolean ignore if system command fails.

    @return: status code of the executed command.
    """
    return control_service(service_name, action='stop',
                           ignore_status=ignore_status)


def sudo_require_password():
    """Test if the process can run sudo command without using password.

    @return: True if the process needs password to run sudo command.

    """
    try:
        run('sudo -n true')
        return False
    except error.CmdError:
        logging.warn('sudo command requires password.')
        return True


def is_in_container():
    """Check if the process is running inside a container.

    @return: True if the process is running inside a container, otherwise False.
    """
    result = run('grep -q "/lxc/" /proc/1/cgroup',
                            verbose=False, ignore_status=True)
    if result.exit_status == 0:
        return True

    # Check "container" environment variable for lxd/lxc containers.
    if os.environ.get('container') == 'lxc':
        return True

    return False


def is_flash_installed():
    """
    The Adobe Flash binary is only distributed with internal builds.
    """
    return (os.path.exists('/opt/google/chrome/pepper/libpepflashplayer.so')
        and os.path.exists('/opt/google/chrome/pepper/pepper-flash.info'))


def verify_flash_installed():
    """
    The Adobe Flash binary is only distributed with internal builds.
    Warn users of public builds of the extra dependency.
    """
    if not is_flash_installed():
        raise error.TestNAError('No Adobe Flash binary installed.')


def is_in_same_subnet(ip_1, ip_2, mask_bits=24):
    """Check if two IP addresses are in the same subnet with given mask bits.

    The two IP addresses are string of IPv4, e.g., '192.168.0.3'.

    @param ip_1: First IP address to compare.
    @param ip_2: Second IP address to compare.
    @param mask_bits: Number of mask bits for subnet comparison. Default to 24.

    @return: True if the two IP addresses are in the same subnet.

    """
    mask = ((2<<mask_bits-1) -1)<<(32-mask_bits)
    ip_1_num = struct.unpack('!I', socket.inet_aton(ip_1))[0]
    ip_2_num = struct.unpack('!I', socket.inet_aton(ip_2))[0]
    return ip_1_num & mask == ip_2_num & mask


def get_ip_address(hostname=None):
    """Get the IP address of given hostname or current machine.

    @param hostname: Hostname of a DUT, default value is None.

    @return: The IP address of given hostname. If hostname is not given then
             we'll try to query the IP address of the current machine and
             return.
    """
    if hostname:
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror as e:
            logging.error(
                'Failed to get IP address of %s, error: %s.', hostname, e)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip


def get_servers_in_same_subnet(host_ip, mask_bits, servers=None,
                               server_ip_map=None):
    """Get the servers in the same subnet of the given host ip.

    @param host_ip: The IP address of a dut to look for devserver.
    @param mask_bits: Number of mask bits.
    @param servers: A list of servers to be filtered by subnet specified by
                    host_ip and mask_bits.
    @param server_ip_map: A map between the server name and its IP address.
            The map can be pre-built for better performance, e.g., when
            allocating a drone for an agent task.

    @return: A list of servers in the same subnet of the given host ip.

    """
    matched_servers = []
    if not servers and not server_ip_map:
        raise ValueError('Either `servers` or `server_ip_map` must be given.')
    if not servers:
        servers = list(server_ip_map.keys())
    # Make sure server_ip_map is an empty dict if it's not set.
    if not server_ip_map:
        server_ip_map = {}
    for server in servers:
        server_ip = server_ip_map.get(server, get_ip_address(server))
        if server_ip and is_in_same_subnet(server_ip, host_ip, mask_bits):
            matched_servers.append(server)
    return matched_servers


def get_restricted_subnet(hostname, restricted_subnets=None):
    """Get the restricted subnet of given hostname.

    @param hostname: Name of the host to look for matched restricted subnet.
    @param restricted_subnets: A list of restricted subnets, default is set to
            RESTRICTED_SUBNETS.

    @return: A tuple of (subnet_ip, mask_bits), which defines a restricted
             subnet.
    """
    if restricted_subnets is None:
        restricted_subnets=RESTRICTED_SUBNETS
    host_ip = get_ip_address(hostname)
    if not host_ip:
        return
    for subnet_ip, mask_bits in restricted_subnets:
        if is_in_same_subnet(subnet_ip, host_ip, mask_bits):
            return subnet_ip, mask_bits


def get_wireless_ssid(hostname):
    """Get the wireless ssid based on given hostname.

    The method tries to locate the wireless ssid in the same subnet of given
    hostname first. If none is found, it returns the default setting in
    CLIENT/wireless_ssid.

    @param hostname: Hostname of the test device.

    @return: wireless ssid for the test device.
    """
    default_ssid = CONFIG.get_config_value('CLIENT', 'wireless_ssid',
                                           default=None)
    host_ip = get_ip_address(hostname)
    if not host_ip:
        return default_ssid

    # Get all wireless ssid in the global config.
    ssids = CONFIG.get_config_value_regex('CLIENT', WIRELESS_SSID_PATTERN)

    # There could be multiple subnet matches, pick the one with most strict
    # match, i.e., the one with highest maskbit.
    matched_ssid = default_ssid
    matched_maskbit = -1
    for key, value in ssids.items():
        # The config key filtered by regex WIRELESS_SSID_PATTERN has a format of
        # wireless_ssid_[subnet_ip]/[maskbit], for example:
        # wireless_ssid_192.168.0.1/24
        # Following line extract the subnet ip and mask bit from the key name.
        match = re.match(WIRELESS_SSID_PATTERN, key)
        subnet_ip, maskbit = match.groups()
        maskbit = int(maskbit)
        if (is_in_same_subnet(subnet_ip, host_ip, maskbit) and
            maskbit > matched_maskbit):
            matched_ssid = value
            matched_maskbit = maskbit
    return matched_ssid


def parse_launch_control_build(build_name):
    """Get branch, target, build_id from the given Launch Control build_name.

    @param build_name: Name of a Launch Control build, should be formated as
                       branch/target/build_id

    @return: Tuple of branch, target, build_id
    @raise ValueError: If the build_name is not correctly formated.
    """
    branch, target, build_id = build_name.split('/')
    return branch, target, build_id


def parse_android_target(target):
    """Get board and build type from the given target.

    @param target: Name of an Android build target, e.g., shamu-eng.

    @return: Tuple of board, build_type
    @raise ValueError: If the target is not correctly formated.
    """
    board, build_type = target.split('-')
    return board, build_type


def parse_launch_control_target(target):
    """Parse the build target and type from a Launch Control target.

    The Launch Control target has the format of build_target-build_type, e.g.,
    shamu-eng or dragonboard-userdebug. This method extracts the build target
    and type from the target name.

    @param target: Name of a Launch Control target, e.g., shamu-eng.

    @return: (build_target, build_type), e.g., ('shamu', 'userdebug')
    """
    match = re.match('(?P<build_target>.+)-(?P<build_type>[^-]+)', target)
    if match:
        return match.group('build_target'), match.group('build_type')
    else:
        return None, None


def is_launch_control_build(build):
    """Check if a given build is a Launch Control build.

    @param build: Name of a build, e.g.,
                  ChromeOS build: daisy-release/R50-1234.0.0
                  Launch Control build: git_mnc_release/shamu-eng

    @return: True if the build name matches the pattern of a Launch Control
             build, False otherwise.
    """
    try:
        _, target, _ = parse_launch_control_build(build)
        build_target, _ = parse_launch_control_target(target)
        if build_target:
            return True
    except ValueError:
        # parse_launch_control_build or parse_launch_control_target failed.
        pass
    return False


def which(exec_file):
    """Finds an executable file.

    If the file name contains a path component, it is checked as-is.
    Otherwise, we check with each of the path components found in the system
    PATH prepended. This behavior is similar to the 'which' command-line tool.

    @param exec_file: Name or path to desired executable.

    @return: An actual path to the executable, or None if not found.
    """
    if os.path.dirname(exec_file):
        return exec_file if os.access(exec_file, os.X_OK) else None
    sys_path = os.environ.get('PATH')
    prefix_list = sys_path.split(os.pathsep) if sys_path else []
    for prefix in prefix_list:
        path = os.path.join(prefix, exec_file)
        if os.access(path, os.X_OK):
            return path


class TimeoutError(error.TestError):
    """Error raised when poll_for_condition() failed to poll within time.

    It may embed a reason (either a string or an exception object) so that
    the caller of poll_for_condition() can handle failure better.
    """

    def __init__(self, message=None, reason=None):
        """Constructor.

        It supports three invocations:
        1) TimeoutError()
        2) TimeoutError(message): with customized message.
        3) TimeoutError(message, reason): with message and reason for timeout.
        """
        self.reason = reason
        if self.reason:
            reason_str = 'Reason: ' + repr(self.reason)
            if message:
                message += '. ' + reason_str
            else:
                message = reason_str

        if message:
            super(TimeoutError, self).__init__(message)
        else:
            super(TimeoutError, self).__init__()


class Timer(object):
    """A synchronous timer to evaluate if timout is reached.

    Usage:
      timer = Timer(timeout_sec)
      while timer.sleep(sleep_interval):
        # do something...
    """
    def __init__(self, timeout):
        """Constructor.

        Note that timer won't start until next() is called.

        @param timeout: timer timeout in seconds.
        """
        self.timeout = timeout
        self.deadline = 0

    def sleep(self, interval):
        """Checks if it has sufficient time to sleep; sleeps if so.

        It blocks for |interval| seconds if it has time to sleep.
        If timer is not ticked yet, kicks it off and returns True without
        sleep.

        @param interval: sleep interval in seconds.
        @return True if it has sleeped or just kicked off the timer. False
                otherwise.
        """
        now = time.time()
        if not self.deadline:
            self.deadline = now + self.timeout
            return True
        if now + interval < self.deadline:
            time.sleep(interval)
            return True
        return False


def poll_for_condition(condition,
                       exception=None,
                       timeout=10,
                       sleep_interval=0.1,
                       desc=None):
    """Polls until a condition is evaluated to true.

    @param condition: function taking no args and returning anything that will
                      evaluate to True in a conditional check
    @param exception: exception to throw if condition doesn't evaluate to true
    @param timeout: maximum number of seconds to wait
    @param sleep_interval: time to sleep between polls
    @param desc: description of default TimeoutError used if 'exception' is
                 None

    @return The evaluated value that caused the poll loop to terminate.

    @raise 'exception' arg if supplied; TimeoutError otherwise
    """
    start_time = time.time()
    while True:
        value = condition()
        if value:
            return value
        if time.time() + sleep_interval - start_time > timeout:
            if exception:
                logging.error('Will raise error %r due to unexpected return: '
                              '%r', exception, value)
                raise exception # pylint: disable=raising-bad-type

            if desc:
                desc = 'Timed out waiting for condition: ' + desc
            else:
                desc = 'Timed out waiting for unnamed condition'
            logging.error(desc)
            raise TimeoutError(message=desc)

        time.sleep(sleep_interval)


def poll_for_condition_ex(condition, timeout=10, sleep_interval=0.1, desc=None):
    """Polls until a condition is evaluated to true or until timeout.

    Similiar to poll_for_condition, except that it handles exceptions
    condition() raises. If timeout is not reached, the exception is dropped and
    poll for condition after a sleep; otherwise, the exception is embedded into
    TimeoutError to raise.

    @param condition: function taking no args and returning anything that will
                      evaluate to True in a conditional check
    @param timeout: maximum number of seconds to wait
    @param sleep_interval: time to sleep between polls
    @param desc: description of the condition

    @return The evaluated value that caused the poll loop to terminate.

    @raise TimeoutError. If condition() raised exception, it is embedded in
           raised TimeoutError.
    """
    timer = Timer(timeout)
    while timer.sleep(sleep_interval):
        reason = None
        try:
            value = condition()
            if value:
                return value
        except BaseException as e:
            reason = e

    if desc is None:
        desc = 'unamed condition'
    if reason is None:
        reason = 'condition evaluted as false'
    to_raise = TimeoutError(message='Timed out waiting for ' + desc,
                            reason=reason)
    logging.error(str(to_raise))
    raise to_raise


def poll_till_condition_holds(condition,
                              exception=None,
                              timeout=10,
                              sleep_interval=0.1,
                              hold_interval=5,
                              desc=None):
    """Polls until a condition is evaluated to true for a period of time

    This function checks that a condition remains true for the 'hold_interval'
    seconds after it first becomes true. If the condition becomes false
    subsequently, the timer is reset. This function will not detect if
    condition becomes false for any period of time less than the sleep_interval.

    @param condition: function taking no args and returning anything that will
                      evaluate to True in a conditional check
    @param exception: exception to throw if condition doesn't evaluate to true
    @param timeout: maximum number of seconds to wait
    @param sleep_interval: time to sleep between polls
    @param hold_interval: time period for which the condition should hold true
    @param desc: description of default TimeoutError used if 'exception' is
                 None

    @return The evaluated value that caused the poll loop to terminate.

    @raise 'exception' arg if supplied; TimeoutError otherwise
    """
    start_time = time.time()
    cond_is_held = False
    cond_hold_start_time = None

    while True:
        value = condition()
        if value:
            if cond_is_held:
                if time.time() - cond_hold_start_time > hold_interval:
                    return value
            else:
                cond_is_held = True
                cond_hold_start_time = time.time()
        else:
            cond_is_held = False

        time_remaining = timeout - (time.time() - start_time)
        if time_remaining < hold_interval:
            if exception:
                logging.error('Will raise error %r due to unexpected return: '
                              '%r', exception, value)
                raise exception # pylint: disable=raising-bad-type

            if desc:
                desc = 'Timed out waiting for condition: ' + desc
            else:
                desc = 'Timed out waiting for unnamed condition'
            logging.error(desc)
            raise TimeoutError(message=desc)

        time.sleep(sleep_interval)


def shadowroot_query(element, action):
    """Recursively queries shadowRoot.

    @param element: element to query for.
    @param action: action to be performed on the element.

    @return JS functions to execute.

    """
    # /deep/ CSS query has been removed from ShadowDOM. The only way to access
    # elements now is to recursively query in each shadowRoot.
    shadowroot_script = """
    function deepQuerySelectorAll(root, targetQuery) {
        const elems = Array.prototype.slice.call(
            root.querySelectorAll(targetQuery[0]));
        const remaining = targetQuery.slice(1);
        if (remaining.length === 0) {
            return elems;
        }

        let res = [];
        for (let i = 0; i < elems.length; i++) {
            if (elems[i].shadowRoot) {
                res = res.concat(
                    deepQuerySelectorAll(elems[i].shadowRoot, remaining));
            }
        }
        return res;
    };
    var testing_element = deepQuerySelectorAll(document, %s);
    testing_element[0].%s;
    """
    script_to_execute = shadowroot_script % (element, action)
    return script_to_execute


def threaded_return(function):
    """
    Decorator to add to a function to get that function to return a thread
    object, but with the added benefit of storing its return value.

    @param function: function object to be run in the thread

    @return a threading.Thread object, that has already been started, is
            recording its result, and can be completed and its result
            fetched by calling .finish()
    """
    def wrapped_t(queue, *args, **kwargs):
        """
        Calls the decorated function as normal, but appends the output into
        the passed-in threadsafe queue.
        """
        ret = function(*args, **kwargs)
        queue.put(ret)

    def wrapped_finish(threaded_object):
        """
        Provides a utility to this thread object, getting its result while
        simultaneously joining the thread.
        """
        ret = threaded_object.get()
        threaded_object.join()
        return ret

    def wrapper(*args, **kwargs):
        """
        Creates the queue and starts the thread, then assigns extra attributes
        to the thread to give it result-storing capability.
        """
        q = six.moves.queue.Queue()
        t = threading.Thread(target=wrapped_t, args=(q,) + args, kwargs=kwargs)
        t.start()
        t.result_queue = q
        t.get = t.result_queue.get
        t.finish = lambda: wrapped_finish(t)
        return t

    # for the decorator
    return wrapper


@threaded_return
def background_sample_until_condition(
        function,
        condition=lambda: True,
        timeout=10,
        sleep_interval=1):
    """
    Records the value of the function until the condition is False or the
    timeout is reached. Runs as a background thread, so it's nonblocking.
    Usage might look something like:

    def function():
        return get_value()
    def condition():
        return self._keep_sampling

    # main thread
    sample_thread = utils.background_sample_until_condition(
        function=function,condition=condition)
    # do other work
    # ...
    self._keep_sampling = False
    # blocking call to get result and join the thread
    result = sample_thread.finish()

    @param function: function object, 0 args, to be continually polled
    @param condition: function object, 0 args, to say when to stop polling
    @param timeout: maximum number of seconds to wait
    @param number of seconds to wait in between polls

    @return a thread object that has already been started and is running in
            the background, whose run must be stopped with .finish(), which
            also returns a list of the results from the sample function
    """
    log = []

    end_time = datetime.datetime.now() + datetime.timedelta(
            seconds = timeout + sleep_interval)

    while condition() and datetime.datetime.now() < end_time:
        log.append(function())
        time.sleep(sleep_interval)
    return log


class metrics_mock(metrics_mock_class.mock_class_base):
    """mock class for metrics in case chromite is not installed."""
    pass


MountInfo = collections.namedtuple('MountInfo', ['root', 'mount_point', 'tags'])


def get_mount_info(process='self', mount_point=None):
    """Retrieves information about currently mounted file systems.

    @param mount_point: (optional) The mount point (a path).  If this is
                        provided, only information about the given mount point
                        is returned.  If this is omitted, info about all mount
                        points is returned.
    @param process: (optional) The process id (or the string 'self') of the
                    process whose mountinfo will be obtained.  If this is
                    omitted, info about the current process is returned.

    @return A generator yielding one MountInfo object for each relevant mount
            found in /proc/PID/mountinfo.
    """
    with open('/proc/{}/mountinfo'.format(process)) as f:
        for line in f.readlines():
            # TODO b:169251326 terms below are set outside of this codebase
            # and should be updated when possible. ("master" -> "main")
            # These lines are formatted according to the proc(5) manpage.
            # Sample line:
            # 36 35 98:0 /mnt1 /mnt2 rw,noatime master:1 - ext3 /dev/root \
            #     rw,errors=continue
            # Fields (descriptions omitted for fields we don't care about)
            # 3: the root of the mount.
            # 4: the mount point.
            # 5: mount options.
            # 6: tags.  There can be more than one of these.  This is where
            #    shared mounts are indicated.
            # 7: a dash separator marking the end of the tags.
            mountinfo = line.split()
            if mount_point is None or mountinfo[4] == mount_point:
                tags = []
                for field in mountinfo[6:]:
                    if field == '-':
                        break
                    tags.append(field.split(':')[0])
                yield MountInfo(root = mountinfo[3],
                                mount_point = mountinfo[4],
                                tags = tags)


# Appended suffix for chart tablet naming convention in test lab
CHART_ADDRESS_SUFFIX = '-tablet'


def get_lab_chart_address(hostname):
    """Convert lab DUT hostname to address of camera box chart tablet"""
    return hostname + CHART_ADDRESS_SUFFIX if is_in_container() else None


def cherry_pick_args(func, args, dargs):
    """Sanitize positional and keyword arguments before calling a function.

    Given a callable (func), an argument tuple and a dictionary of keyword
    arguments, pick only those arguments which the function is prepared to
    accept and return a new argument tuple and keyword argument dictionary.

    Args:
      func: A callable that we want to choose arguments for.
      args: A tuple of positional arguments to consider passing to func.
      dargs: A dictionary of keyword arguments to consider passing to func.
    Returns:
      A tuple of: (args tuple, keyword arguments dictionary)
    """
    # Cherry pick args:
    if hasattr(func, "func_code"):
        # Moock doesn't have __code__ in either py2 or 3 :(
        flags = func.func_code.co_flags
    else:
        flags = func.__code__.co_flags

    if flags & 0x04:
        # func accepts *args, so return the entire args.
        p_args = args
    else:
        p_args = ()

    # Cherry pick dargs:
    if flags & 0x08:
        # func accepts **dargs, so return the entire dargs.
        p_dargs = dargs
    else:
        # Only return the keyword arguments that func accepts.
        p_dargs = {}
        for param in get_nonstar_args(func):
            if param in dargs:
                p_dargs[param] = dargs[param]

    return p_args, p_dargs


def cherry_pick_call(func, *args, **dargs):
    """Cherry picks arguments from args/dargs based on what "func" accepts
    and calls the function with the picked arguments."""
    p_args, p_dargs = cherry_pick_args(func, args, dargs)
    return func(*p_args, **p_dargs)


def get_nonstar_args(func):
    """Extract all the (normal) function parameter names.

    Given a function, returns a tuple of parameter names, specifically
    excluding the * and ** parameters, if the function accepts them.

    @param func: A callable that we want to chose arguments for.

    @return: A tuple of parameters accepted by the function.
    """
    return func.__code__.co_varnames[:func.__code__.co_argcount]

def crc8(buf):
    """Calculate CRC8 for a given int list.

    This is a simple version of CRC8.

    Args:
      buf: A list of byte integer
    Returns:
      A crc value in integer
    """

    _table_crc8 = [ 0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15,
                    0x38, 0x3f, 0x36, 0x31, 0x24, 0x23, 0x2a, 0x2d,
                    0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65,
                    0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d,
                    0xe0, 0xe7, 0xee, 0xe9, 0xfc, 0xfb, 0xf2, 0xf5,
                    0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
                    0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85,
                    0xa8, 0xaf, 0xa6, 0xa1, 0xb4, 0xb3, 0xba, 0xbd,
                    0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2,
                    0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea,
                    0xb7, 0xb0, 0xb9, 0xbe, 0xab, 0xac, 0xa5, 0xa2,
                    0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
                    0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32,
                    0x1f, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0d, 0x0a,
                    0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42,
                    0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a,
                    0x89, 0x8e, 0x87, 0x80, 0x95, 0x92, 0x9b, 0x9c,
                    0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
                    0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec,
                    0xc1, 0xc6, 0xcf, 0xc8, 0xdd, 0xda, 0xd3, 0xd4,
                    0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c,
                    0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44,
                    0x19, 0x1e, 0x17, 0x10, 0x05, 0x02, 0x0b, 0x0c,
                    0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
                    0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b,
                    0x76, 0x71, 0x78, 0x7f, 0x6a, 0x6d, 0x64, 0x63,
                    0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b,
                    0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13,
                    0xae, 0xa9, 0xa0, 0xa7, 0xb2, 0xb5, 0xbc, 0xbb,
                    0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8d, 0x84, 0x83,
                    0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb,
                    0xe6, 0xe1, 0xe8, 0xef, 0xfa, 0xfd, 0xf4, 0xf3,
                  ]
    if not isinstance(buf, list):
        raise error.TestError('buf should be an integer list.')
    if not all(isinstance(i, int) for i in buf):
        raise error.TestError('buf should contain integers only.')

    rv = 0
    for i in buf:
        rv = _table_crc8[ (rv ^ i) & 0xff ]
    return rv

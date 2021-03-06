# Copyright (c) 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET

import common
from autotest_lib.client.bin import test, utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib import file_utils
from autotest_lib.client.cros import constants


class ChromeBinaryTest(test.test):
    """
    Base class for tests to run chrome test binaries without signing in and
    running Chrome.
    """

    CHROME_TEST_DEP = 'chrome_test'
    CHROME_SANDBOX = '/opt/google/chrome/chrome-sandbox'
    COMPONENT_LIB = '/opt/google/chrome/lib'
    home_dir = None
    cr_source_dir = None
    test_binary_dir = None

    def setup(self):
        """
        Sets up a test.
        """
        self.job.setup_dep([self.CHROME_TEST_DEP])

    def initialize(self):
        """
        Initializes members after setup().
        """
        test_dep_dir = os.path.join(self.autodir, 'deps', self.CHROME_TEST_DEP)
        self.job.install_pkg(self.CHROME_TEST_DEP, 'dep', test_dep_dir)

        self.cr_source_dir = '%s/test_src' % test_dep_dir
        self.test_binary_dir = '%s/out/Release' % self.cr_source_dir
        # If chrome is a component build then need to create a symlink such
        # that the _unittest binaries can find the chrome component libraries.
        Release_lib = os.path.join(self.test_binary_dir, 'lib')
        if os.path.isdir(self.COMPONENT_LIB):
            logging.info('Detected component build. This assumes binary '
                         'compatibility between chrome and *unittest.')
            if not os.path.islink(Release_lib):
                os.symlink(self.COMPONENT_LIB, Release_lib)
        self.home_dir = tempfile.mkdtemp()

    def cleanup(self):
        """
        Cleans up working directory after run.
        """
        if self.home_dir:
            shutil.rmtree(self.home_dir, ignore_errors=True)

    def get_chrome_binary_path(self, binary_to_run):
        """
        Gets test binary's full path.

        @returns full path of the test binary to run.
        """
        return os.path.join(self.test_binary_dir, binary_to_run)

    def parse_fail_reason(self, err, gtest_xml):
        """
        Parses reason of failure from CmdError and gtest result.

        @param err: CmdError raised from utils.system().
        @param gtest_xml: filename of gtest result xml.
        @returns reason string
        """
        reasons = {}

        # Parse gtest result.
        if os.path.exists(gtest_xml):
            tree = ET.parse(gtest_xml)
            root = tree.getroot()
            for suite in root.findall('testsuite'):
                for case in suite.findall('testcase'):
                    failure = case.find('failure')
                    if failure is None:
                        continue
                    testname = '%s.%s' % (suite.get('name'), case.get('name'))
                    reasons[testname] = failure.attrib['message']

        # Parse messages from chrome's test_launcher.
        # This provides some information not available from gtest, like timeout.
        for line in err.result_obj.stdout.splitlines():
            m = re.match(r'\[\d+/\d+\] (\S+) \(([A-Z ]+)\)$', line)
            if not m:
                continue
            testname, reason = m.group(1, 2)
            # Existing reason from gtest has more detail, don't overwrite.
            if testname not in reasons:
                reasons[testname] = reason

        if reasons:
            message = '%d failures' % len(reasons)
            for testname, reason in sorted(reasons.items()):
                message += '; <%s>: %s' % (testname, reason.replace('\n', '; '))
            return message

        return 'Unable to parse fail reason: ' + str(err)

    def run_chrome_test_binary(self,
                               binary_to_run,
                               extra_params='',
                               prefix='',
                               as_chronos=True,
                               timeout=None):
        """
        Runs chrome test binary.

        @param binary_to_run: The name of the browser test binary.
        @param extra_params: Arguments for the browser test binary.
        @param prefix: Prefix to the command that invokes the test binary.
        @param as_chronos: Boolean indicating if the tests should run in a
            chronos shell.
        @param timeout: timeout in seconds

        @raises: error.TestFail if there is error running the command.
        @raises: CmdTimeoutError: the command timed out and |timeout| is
            specified and not None.
        """
        gtest_xml = tempfile.mktemp(prefix='gtest_xml', suffix='.xml')
        binary_path = self.get_chrome_binary_path(binary_to_run)
        env_vars = ' '.join([
            'HOME=' + self.home_dir,
            'CR_SOURCE_ROOT=' + self.cr_source_dir,
            'CHROME_DEVEL_SANDBOX=' + self.CHROME_SANDBOX,
            'GTEST_OUTPUT=xml:' + gtest_xml,
            ])
        cmd = ' '.join([env_vars, prefix, binary_path, extra_params])

        try:
            if as_chronos:
                utils.system("su chronos -c '%s'" % cmd,
                             timeout=timeout)
            else:
                utils.system(cmd, timeout=timeout)
        except error.CmdError as e:
            return_code = e.result_obj.exit_status
            if return_code == 126:
                path_permission = '; '.join(
                    file_utils.recursive_path_permission(binary_path))
                fail_reason = ('Cannot execute command %s. Permissions: %s' %
                               (binary_path, path_permission))
            elif return_code == 127:
                fail_reason = ('Command not found: %s' % binary_path)
            else:
                fail_reason = self.parse_fail_reason(e, gtest_xml)

            raise error.TestFail(fail_reason)


def nuke_chrome(func):
    """
    Decorator to nuke the Chrome browser processes.
    """

    def wrapper(*args, **kargs):
        """
        Nukes Chrome browser processes before invoking func().

        Also, restarts Chrome after func() returns.
        """
        open(constants.DISABLE_BROWSER_RESTART_MAGIC_FILE, 'w').close()
        try:
            try:
                utils.nuke_process_by_name(name=constants.BROWSER,
                                           with_prejudice=True)
            except error.AutoservPidAlreadyDeadError:
                pass
            return func(*args, **kargs)
        finally:
            # Allow chrome to be restarted again later.
            os.unlink(constants.DISABLE_BROWSER_RESTART_MAGIC_FILE)

    return wrapper

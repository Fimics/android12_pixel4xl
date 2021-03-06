# Copyright (c) 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros.bluetooth import bluetooth_semiauto_helper


class bluetooth_AdapterHealth(
        bluetooth_semiauto_helper.BluetoothSemiAutoHelper):
    """Checks whether the Bluetooth adapter is present and working."""
    version = 1

    def _find_kernel_errors(self):
        """Fail test for any suspicious log entries from kernel.

        Ignore some known errors in order to find new ones.

        """
        fail_terms = ['[^a-z]err[^a-z]']
        ignore_terms = ['RFKILL control',
                        '"Service Changed" characteristic',
                        'Unknown Evt ID: 19',
                        'Failed to set privacy: Rejected']

        log_cmd = 'grep -i bluetooth /var/log/messages'
        for term in ignore_terms:
            log_cmd += ' | grep -v \'%s\'' % term

        for term in fail_terms:
            search_cmd = '%s | grep -i \'%s\'' % (log_cmd, term)
            log_entries = utils.run(search_cmd, ignore_status=True).stdout
            if len(log_entries) > 0:
                log_entries = [l for l in log_entries.split('\n') if l != '']
                logging.info(log_entries)
                self.collect_logs('Bluetooth kernel error')

                # Add snippet of the log to the error message
                # unless there are many errors (>5)
                # This is helpful when looking at stainless results
                error_str = 'Bluetooth kernel error found!'
                if len(log_entries) <= 5:
                    error_str = error_str + ' | '
                    for l in log_entries:
                        error_str = error_str +  l.split('ERR')[1] + ' | '

                raise error.TestFail(error_str)

    def warmup(self):
        """Overwrite parent warmup; no need to log in."""
        pass

    def run_once(self):
        """Entry point of this test."""
        if not self.supports_bluetooth():
            return

        # Start btmon running.
        self.start_dump()

        self.poll_adapter_presence()

        # Enable then disable adapter.
        self.set_adapter_power(True)
        self.set_adapter_power(False)

        # Check for errors in logs.
        self._find_kernel_errors()

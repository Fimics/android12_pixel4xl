# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os

from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib import utils
from autotest_lib.server.cros.faft.firmware_test import FirmwareTest


class platform_Flashrom(FirmwareTest):
    """
    Test flashrom works correctly by calling
    chromeos-firmwareupdate --mode=factory.
    """
    version = 1


    def initialize(self, host, cmdline_args):
        # This test assume the system already have the latest RW from
        # shellball.  If you not sure, run chromeos-firmware --mode=factory.
        # Device should have WP disable.

        # Parse arguments from command line
        dict_args = utils.args_to_dict(cmdline_args)
        super(platform_Flashrom, self).initialize(host, cmdline_args)

    def run_cmd(self, command, checkfor=''):
        """
        Log and execute command and return the output.

        @param command: Command to execute on device.
        @param checkfor: If not emmpty, fail test if checkfor not in output.
        @returns the output of command.
        """
        command = command + ' 2>&1'
        logging.info('Execute %s', command)
        output = self.faft_client.system.run_shell_command_get_output(command)
        logging.info('Output >>> %s <<<', output)
        if checkfor and checkfor not in '\n'.join(output):
            raise error.TestFail('Expect %s in output of %s' %
                                 (checkfor, '\n'.join(output)))
        return output

    def _check_wp_disable(self):
        """Check firmware is write protect disabled."""
        self.run_cmd('flashrom -p host --wp-status', checkfor='is disabled')
        if self.faft_config.chrome_ec:
            self.run_cmd('flashrom -p ec --wp-status', checkfor='is disabled')
        if self.faft_config.chrome_usbpd:
            self.run_cmd('flashrom -p ec:type=pd --wp-status',
                         checkfor='is disabled')

    def _get_region(self, fmap_filename, region):
        """Get region start and size from fmap.

        @param fmap_filename: Path to dump of FMAP.
        @param region: The region name.
        @return tuple of start and size for the region.
        """
        output = self.run_cmd('dump_fmap -p %s %s' % (fmap_filename, region))
        _, start, size = output[0].split()
        return int(start), int(size)

    def run_once(self, dev_mode=True):
        """Main test logic"""
        # 1) Check SW WP is disabled.
        self._check_wp_disable()

        # Output location on DUT.
        # Set if you want to preserve output content for debug.
        tmpdir = os.getenv('DUT_TMPDIR')
        if not tmpdir: tmpdir = '/tmp'

        # 2) Erase RW section B.  Needed CL 329549 starting with R51-7989.0.0.
        # before this change -E erase everything.
        self.run_cmd('flashrom -E -i RW_SECTION_B', 'SUCCESS')

        # 3) Reinstall RW B (Test flashrom)
        self.run_cmd('chromeos-firmwareupdate --mode=factory', 'SUCCESS')

        # 4) Check that device can be rebooted.
        self.switcher.mode_aware_reboot()

        # 5) Compare flash section B vs shellball section B
        # 5.1) Extract shellball RW section B form the appropriate bios.bin
        # found the firmware tarball on the DUT.
        self.faft_client.updater.extract_shellball()
        shball_bios = os.path.join(
            self.faft_client.updater.get_work_path(),
            self.faft_client.updater.get_bios_relative_path())
        # Temp file to store a section read from the chip.
        shball_rw_b = os.path.join(
            self.faft_client.updater.get_work_path(),
            'shball_rw_b.bin')
        logging.info('Using fw image %s, temp file %s',
                     shball_bios, shball_rw_b)

        # Extract FMAP
        fmap = os.path.join(tmpdir, 'fmap.bin')
        self.run_cmd('flashrom -r -i FMAP:%s' % fmap, 'SUCCESS')

        # Extract RW B, offset detail
        # Figure out section B start byte and size.
        (Bstart, Blen) = self._get_region(fmap, 'RW_SECTION_B')
        self.run_cmd('dd bs=1 skip=%d count=%d if=%s of=%s 2>&1'
                     % (Bstart, Blen, shball_bios, shball_rw_b), '%d bytes' % Blen)

        # 5.2) Extract flash RW section B.
        # skylake cannot read only section B, see http://crosbug.com/p/52061
        rw_b2 = os.path.join(tmpdir, 'rw_b2.bin')
        self.run_cmd('flashrom -r -i RW_SECTION_B:%s' % rw_b2, 'SUCCESS')

        # 5.3) Compare output of 5.1 vs 5.2
        result_output = self.run_cmd('cmp %s %s' % (shball_rw_b, rw_b2))
        logging.info('cmp %s %s == %s', shball_rw_b, rw_b2, result_output)

        # 6) Report result.
        if ''.join(result_output) != '':
            raise error.TestFail('Mismatch between %s and %s' % (shball_rw_b, rw_b2))

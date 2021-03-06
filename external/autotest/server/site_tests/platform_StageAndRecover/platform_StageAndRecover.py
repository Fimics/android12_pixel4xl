# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

from autotest_lib.server import test
from autotest_lib.client.common_lib import error

class platform_StageAndRecover(test.test):
    """Installs the same version recovery image onto a servo-connected DUT."""
    version = 1

    _INSTALL_DELAY_TIMEOUT = 540
    _TEST_IMAGE_BOOT_DELAY = 180
    _USB_PARTITION = '/dev/sda1'
    _MOUNT_PATH = '/media/removable'
    _VERIFY_STR = 'ChromeosChrootPostinst complete'
    _RECOVERY_LOG = '/recovery_logs*/recovery.log'
    _SET_DELAY = 2

    def cleanup(self):
        """ Clean up by switching servo usb towards servo host. """
        self.host.servo.switch_usbkey('host')


    def initialize(self, host):
        """ Preparing servo to see only DUT_HUB1.
        Avoiding peripherals plugged at this servo port.
        """
        host.servo.set('prtctl4_pwren','on')
        time.sleep(self._SET_DELAY)
        host.servo.set('usb_mux_oe3', 'off')
        time.sleep(self._SET_DELAY)
        host.servo.set('usb_mux_oe1', 'off')
        time.sleep(self._SET_DELAY)

        # Switch usb_mux_sel1 to enumerate as /dev/sda
        host.servo.set('usb_mux_oe1', 'on')
        time.sleep(self._SET_DELAY)
        host.servo.set('usb_mux_sel1', 'servo_sees_usbkey')
        time.sleep(self._SET_DELAY)
        try:
            host.servo.system('test -e /dev/sda')
            host.servo.system('mkdir -p %s' %(self._MOUNT_PATH))
        except error.AutoservRunError:
            servo_disk = host.servo.system_output('fdisk -l', ignore_status=True )
            usb_control = host.servo.system_output('dut-control | grep mux',
                                                    ignore_status=True)
            logging.info('Servo disk info : %s', servo_disk)
            logging.info('Servo USB controls: %s', usb_control)
            raise error.TestError('Issue with servo USB mount path %s'
                                  % (self._USB_PARTITION))


    def stage_copy_recover_with(self, artifact):
        """ Stage image, copy image to servo usb, and 'rec' boot the device.

        @param artifact: image type - recovery_image or test_image
        """
        # Stage the image on dev server
        _, image_path = self.host.stage_image_for_servo(
            self.release_builder_path,
            artifact=artifact)
        logging.info('%s staged at %s', artifact, image_path)

        # Reimage servo USB
        self.host.servo.image_to_servo_usb(image_path,
                                           make_image_noninteractive=True)
        self.host.servo.set('usb_mux_sel1', 'dut_sees_usbkey')
        time.sleep(self._SET_DELAY)

        # Boot DUT in recovery mode for image to install
        self.host.servo.boot_in_recovery_mode()


    def wait_for_dut_ping_after(self, process, timeout):
        """ Wait for DUT after reimaging or rebooting.

        @param process: process to check timeout for
        @param timeout: timeout to wait for DUT to answer to ping_wait_up

        @raise error.TestFail: if timeout is reached
        """
        logging.info('Started %s. Will wait up to %d seconds to complete',
                     process, timeout)
        start_time = time.time()
        result = self.host.ping_wait_up(timeout=timeout)
        if result:
            logging.info('Device came back up successfully in %d seconds.',
                         time.time() - start_time)
        else:
            if process.find('TEST_IMAGE') != -1:
                logging.info('Host failed to come back after %s '
                             'in %d seconds.' % (process, timeout))
            else:
                self.error_messages.append('Host failed to come back after %s '
                                           'in %d seconds.' % (process, timeout))
        return result


    def verify_recovery_log(self):
        """ Mount USB partition to servo and verify the recovery log. """
        recovery_info = ''
        self.host.servo.set('usb_mux_oe3', 'off')
        time.sleep(self._SET_DELAY)
        self.host.servo.set('usb_mux_sel1', 'servo_sees_usbkey')
        time.sleep(self._SET_DELAY)
        try:
            self.host.servo.system('mount -r %s %s'
                                   % (self._USB_PARTITION, self._MOUNT_PATH))
        except error.AutoservRunError:
            servo_disk = self.host.servo.system_output('fdisk -l', ignore_status=True)
            logging.info('Servo disk info : %s', servo_disk)
            raise error.TestError('Issue with servo USB mount path %s'
                                  % (self._USB_PARTITION))
        recovery_info = self.host.servo.system_output('cat %s%s'
                % (self._MOUNT_PATH, self._RECOVERY_LOG), ignore_status=True)
        if recovery_info:
            if (recovery_info.find(self._VERIFY_STR) != -1):
                logging.info('Recovery log successfully verified.')
            else:
                log_list = recovery_info.split('\n')
                failure_tag = 'Failed Command'
                reasons = [line for line in log_list if failure_tag in line]
                logging.info('Recovery log:\n%s\n', recovery_info)
                self.error_messages.append(' %s ' % (','.join(reasons)))
        else:
            self.error_messages.append('Recovery log is missing.')
        self.host.servo.system('umount %s' % (self._MOUNT_PATH))


    def run_once(self, host):
        """ Runs the test."""
        self.host = host
        self.error_messages = []

        self.release_builder_path = self.host.get_release_builder_path()

        self.stage_copy_recover_with('recovery_image')
        self.wait_for_dut_ping_after('RECOVERY', self._INSTALL_DELAY_TIMEOUT)
        self.verify_recovery_log()

        try:
            # Post-recovery exception handling : Test image installation is
            # out of scope of the test verification and these failures should
            # not be a reason to error out.
            self.stage_copy_recover_with('test_image')

            # Install the test image back on DUT and reboot
            if self.wait_for_dut_ping_after('TEST_IMAGE RECOVERY BOOT FROM USB',
                                            self._TEST_IMAGE_BOOT_DELAY):
                if self.host.wait_up(timeout=self._TEST_IMAGE_BOOT_DELAY):
                    self.host.run('chromeos-install --yes', ignore_status=True,
                              timeout=self._INSTALL_DELAY_TIMEOUT)
                self.host.reboot()
        except error.AutoservRunError:
            pass

        if self.error_messages:
            raise error.TestFail('Failures: %s' % ' '.join(self.error_messages))

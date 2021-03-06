# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import pipes
import os
import re
import shutil
import subprocess
import tempfile

from autotest_lib.client.common_lib.cros import dev_server
from autotest_lib.client.common_lib import error
from autotest_lib.server import test
from autotest_lib.server import utils

# 2 & 4 are default partitions, and the system boots from one of them.
# Code from chromite/scripts/deploy_chrome.py
KERNEL_A_PARTITION = 2
KERNEL_B_PARTITION = 4

SIMG2IMG_PATH = '/usr/bin/simg2img'


class provision_CheetsUpdate(test.test):
    """
    Update Android build On the target DUT.

    This test is designed for ARC++ Treehugger style CQ to update Android image
    on the DUT.
    """
    version = 1


    def initialize(self):
        self.android_build_path = None
        self.push_to_device_dir_path = None
        self.__build_temp_dir = None


    def download_android_build(self, android_build, ds):
        """
        Download the Android test build from the dev server.

        @param android_build: Android build to test.
        @param ds: Dev server instance for downloading the test build.
        """
        build_filename = self.generate_android_build_filename(android_build)
        logging.info('Generated build name: %s', build_filename)
        branch, target, build_id = (
                utils.parse_launch_control_build(android_build))
        ds.stage_artifacts(target, build_id, branch, artifacts=['zip_images'])
        zip_image = ds.get_staged_file_url(
                build_filename,
                target,
                build_id,
                branch)
        logging.info('Downloading the test build.')
        test_filepath = os.path.join(self.__build_temp_dir, build_filename)
        logging.info('Android test file download path: %s', test_filepath)
        logging.info('Zip image: %s', zip_image)
        # Timeout if Android build downloading takes more than 10 minutes.
        ds.download_file(zip_image, test_filepath, timeout=10)
        if not os.path.exists(test_filepath):
            raise error.TestFail(
                    'Android test build %s download failed' % test_filepath)
        self.android_build_path = test_filepath

    def download_sepolicy(self, android_build, ds):
        """
        Download sepolicy.zip artifact of an Android build.

        @param android_build: Android build to test
        @param ds: Dev server instance for downloading the test build.
        """
        _SEPOLICY_FILENAME = 'sepolicy.zip'
        branch, target, build_id = (
                utils.parse_launch_control_build(android_build))
        try:
            ds.stage_artifacts(target, build_id, branch, artifacts=[_SEPOLICY_FILENAME])
        except dev_server.DevServerException as e:
            # e is DevServerException with response HTML in the message.
            # We can't simply match ArtifactDownloadError by error type.
            # Instead, we could only use string match to determine the server error type.
            if 'ArtifactDownloadError: No artifact found' in str(e):
                self.sepolicy = None
                logging.info(
                        'No artifact sepolicy.zip. Fallback to Android policy only')
                return
            else:
                raise e
        sepolicy_zip_url = ds.get_staged_file_url(
                _SEPOLICY_FILENAME,
                target,
                build_id,
                branch)
        logging.info('Downloading the sepolicy.zip.')
        sepolicy_zip_filepath = os.path.join(self.__build_temp_dir, 'sepolicy.zip')
        ds.download_file(sepolicy_zip_url, sepolicy_zip_filepath, timeout=10)
        if not os.path.exists(sepolicy_zip_filepath):
            raise error.TestFail('Android sepolicy.zip download failed')
        self.sepolicy = sepolicy_zip_filepath


    def download_push_to_device(self, android_build, ds):
        """
        Download and unarchive push_to_device artifact from the dev server.

        @param android_build:
            Android build containing the push_to_device artifact.
        @param ds: Dev server instance for downloading push_to_device.
        """
        logging.info('Downloading push_to_device.zip.')
        branch, target, build_id = (
                utils.parse_launch_control_build(android_build))
        ds.stage_artifacts(
                target, build_id, branch, artifacts=['push_to_device_zip'])
        zip_url = ds.get_staged_file_url(
                'push_to_device.zip', target, build_id, branch)
        zip_filepath = os.path.join(self.__build_temp_dir, 'push_to_device.zip')
        dir_filepath = os.path.join(self.__build_temp_dir, 'push_to_device')
        ds.download_file(zip_url, zip_filepath, timeout=10)
        if not os.path.exists(zip_filepath):
            raise error.TestFail('Failed to download %s' % zip_url)
        logging.info('Unarchiving push_to_device.zip to %s', dir_filepath)
        cmd = ['unzip', zip_filepath, '-d', dir_filepath]
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise error.TestFail('unzip failed due to: %s' % e.output)
        self.push_to_device_dir_path = dir_filepath


    def remove_rootfs(self, host):
        """
        Remove rootfs verification on DUT.

        Removing rootfs is required to push a new Android image to DUT.

        @param host: DUT on which rootfs needs to be disabled.
        """
        logging.info('Disabling rootfs on the DUT.')
        cmd = ('/usr/share/vboot/bin/make_dev_ssd.sh --partitions %d '
               '--remove_rootfs_verification --force')
        for partition in (KERNEL_A_PARTITION, KERNEL_B_PARTITION):
            cmd_with_partition = cmd % partition
            logging.info(cmd_with_partition)
            host.run(cmd_with_partition)
        host.reboot()


    def generate_android_build_filename(self, android_build):
        """
        Parse Android build version to generate the build file name.

        @param android_build: android build info with branch and build type.
                              e.g. git_mnc-dr-arc-dev/cheets_arm-user/P3909418
                              e.g. git_mnc-dr-arc-dev/cheets_x86-user/P3909418

        @return Android test file name to download and update on the DUT.
        """
        m = re.findall(r'cheets_\w+|P?\d+$', android_build)
        if m:
            return m[0] + '-img-' + m[1] + '.zip'
        else:
            raise error.TestFail(
                    'Android build arg %s is missing build version info.' %
                    android_build)


    def run_push_to_device(self, host):
        """
        Run push_to_device command to push the test Android build to the DUT.

        @param host: DUT on which the new Android image needs to be pushed.
        """
        cmd = ['python3',
               os.path.join(self.push_to_device_dir_path, 'push_to_device.py'),
               '--use-prebuilt-file',
               self.android_build_path,
               '--simg2img-path',
               SIMG2IMG_PATH,
               '--secilc-path',
               os.path.join(self.push_to_device_dir_path, 'bin', 'secilc'),
               '--mksquashfs-path',
               os.path.join(self.push_to_device_dir_path, 'bin', 'mksquashfs'),
               '--unsquashfs-path',
               os.path.join(self.push_to_device_dir_path, 'bin', 'unsquashfs'),
               '--shift-uid-py-path',
               os.path.join(self.push_to_device_dir_path, 'shift_uid.py'),
               host.hostname,
               '--loglevel',
               'DEBUG']
        if self.sepolicy:
            cmd.extend(['--sepolicy-artifacts-path', self.sepolicy])
        try:
            logging.info('Running push to device:')
            logging.info(
                    '%s',
                    ' '.join(pipes.quote(arg) for arg in cmd))
            output = subprocess.check_output(
                    cmd,
                    stderr=subprocess.STDOUT)
            logging.info(output)
        except subprocess.CalledProcessError as e:
            logging.error(
                    'Error while executing %s',
                    ' '.join(pipes.quote(arg) for arg in cmd))
            logging.error(e.output)
            raise error.TestFail(
                    'Pushing Android test build failed due to: %s' %
                    e.output)


    def run_once(self, host, value=None):
        """
        Installs test ChromeOS version and Android version `value` on `host`.

        This method is invoked by the test control file to start the
        provisioning test.

        @param host: DUT on which the test to be run.
        @param value: contains Android build info to test.
                      git_nyc-arc/cheets_x86-user/3512523
        """
        logging.debug('Start provisioning %s to %s.', host, value)

        if not value:
            raise error.TestFail('No build provided.')

        cheets_prefix = host.host_version_prefix(value)
        info = host.host_info_store.get()
        try:
            host_android_build = info.get_label_value(cheets_prefix)
            logging.info('Cheets build from cheets-version: %s.',
                         host_android_build)
        except:
            # In case the DUT has never run cheets tests before, there might not
            # be cheets build label set.
            host_android_build = None
        # provision_QuickProvision can update the cheets version and the
        # cheets-version label might not have been updated so checking the
        # cheets version installed on the DUT.
        dut_arc_version = host.get_arc_version()
        logging.info('Cheets build installed on the DUT from lsb-release: %s.',
                     dut_arc_version)
        if dut_arc_version and dut_arc_version in value:
            # Update the cheets version label in case the DUT label and
            # installed cheets version aren't matching.
            if host_android_build != value:
                info.set_version_label(cheets_prefix, value)
                host.host_info_store.commit(info)
            # If the installed cheets version is same as the test version, emitting
            # an INFO line.
            self.job.record('INFO', None, None, 'Host already running %s.' % value)
            return
        else:
            logging.info('Updating ARC++ build from %s to %s.',
                         host_android_build,
                         value)
            self.remove_rootfs(host)
            logging.info('Setting up devserver.')
            ds = dev_server.AndroidBuildServer.resolve(value)
            self.__build_temp_dir = tempfile.mkdtemp()
            self.download_android_build(value, ds)
            self.download_push_to_device(value, ds)
            self.download_sepolicy(value, ds)
            self.run_push_to_device(host)
            info = host.host_info_store.get()
            logging.info('Updating DUT version label: %s:%s', cheets_prefix, value)
            info.clear_version_labels(cheets_prefix)
            info.set_version_label(cheets_prefix, value)
            host.host_info_store.commit(info)


    def cleanup(self):
        if self.android_build_path and os.path.exists(self.android_build_path):
            try:
                logging.info(
                        'Deleting Android build dir at %s',
                        self.__build_temp_dir)
                shutil.rmtree(self.__build_temp_dir)
            except OSError as e:
                raise error.TestFail('%s' % e)

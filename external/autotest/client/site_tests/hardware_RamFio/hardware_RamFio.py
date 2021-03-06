# Copyright (c) 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.client.bin import test
from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import service_stopper


class hardware_RamFio(test.test):
    """
    Create ram disk and use FIO to test for ram throughput
    """

    version = 1

    _MB = 1024 * 1024
    _DEFAULT_SIZE = 1024 * _MB
    _RESERVED_RAM_SIZE = 200 * _MB
    _RAMDISK = '/tmp/ramdisk'
    _RAMFS_OVERHEAD = 0.2

    def initialize(self):
        # This test grabs a lot of system memory. Lets move Chrome out of the
        # picture to avoid interference with OOM killer.
        self._services = service_stopper.ServiceStopper(['ui'])
        self._services.stop_services()

    def cleanup(self):
        if self._services:
            self._services.restore_services()

    def run_once(self, size=_DEFAULT_SIZE, requirements=None, dry_run=False):
        """Call hardware_StorageFio to test on ram drive

        @param size: size to test in byte
                     0 means all usable memory
        @param requirements: requirement to pass to hardware_StorageFio
        """
        usable_mem = utils.usable_memtotal() * 1024
        logging.info('Found %d bytes of usable memory.', usable_mem)
        # Assume 20% overhead with ramfs.
        usable_mem *= 1 - self._RAMFS_OVERHEAD

        # crbug.com/762315 Reserved 200 MiB to prevent OOM error.
        if usable_mem <= self._RESERVED_RAM_SIZE:
            raise error.TestNAError(
                'Usable memory (%d MiB) is less than reserved size (%d MiB).' %
                (usable_mem / self._MB, self._RESERVED_RAM_SIZE / self._MB))
        usable_mem -= self._RESERVED_RAM_SIZE

        if size == 0:
            size = usable_mem
        elif usable_mem < size:
            logging.info('Not enough memory. Want: %d, Usable: %d', size,
                         usable_mem)
            size = usable_mem
        self.write_perf_keyval({'Size': size})

        if dry_run:
            return

        utils.run('mkdir -p %s' % self._RAMDISK)
        # Don't throw an exception on errors.
        result = utils.run('mount -t ramfs -o context=u:object_r:tmpfs:s0 '
                           'ramfs %s' % self._RAMDISK, ignore_status = True)
        if result.exit_status:
            logging.info('cannot mount ramfs with context=u:object_r:tmpfs:s0,'
                         ' trying plain mount')
            # Try again without selinux options.  This time fail on error.
            utils.run('mount -t ramfs ramfs %s' % self._RAMDISK)

        self.job.run_test('hardware_StorageFio',
                          dev='%s/test_file' % self._RAMDISK,
                          size=size,
                          requirements=requirements)

        utils.run('umount %s' % self._RAMDISK)

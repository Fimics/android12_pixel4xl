# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import yaml

class ParseKnownCTSFailures(object):
    """A class to parse known failures in CTS test."""

    def __init__(self, failure_files):
        self.waivers_yaml = self._load_failures(failure_files)

    def _validate_waiver_config(self, arch, board, bundle_abi, sdk_ver,
                                first_api_level, config):
        """Validate if the test environment matches the test config.

        @param arch: DUT's arch type.
        @param board: DUT's board name.
        @param bundle_abi: The test's abi type.
        @param sdk_ver: DUT's Android SDK version
        @param first_api_level: DUT's Android first API level.
        @param config: config for an expected failing test.
        @return True if test arch or board is part of the config, else False.
        """
        # Map only the versions that ARC releases care.
        sdk_ver_map = {25: 'N', 28: 'P', 30: 'R'}

        # 'all' applies to all devices.
        # 'x86' or 'arm' applies to the DUT's architecture.
        # board name like 'eve' or 'kevin' applies to the DUT running the board.
        dut_config = ['all', arch, board]
        # 'nativebridge' applies to the case running ARM CTS on x86 devices.
        if bundle_abi and bundle_abi != arch:
            dut_config.append('nativebridge')
        # 'N' or 'P' or 'R' applies to the device running that Android version.
        if sdk_ver in sdk_ver_map:
            dut_config.append(sdk_ver_map[sdk_ver])
        # 'shipatN' or 'shipatP' or 'shipatR' applies to those originally
        # launched at that Android version.
        if first_api_level in sdk_ver_map:
            dut_config.append('shipat' + sdk_ver_map[first_api_level])
        return len(set(dut_config).intersection(config)) > 0

    def _load_failures(self, failure_files):
        """Load failures from files.

        @param failure_files: files with failure configs.
        @return a dictionary of failures config in yaml format.
        """
        waivers_yaml = {}
        for failure_file in failure_files:
            try:
                logging.info('Loading expected failure file: %s.', failure_file)
                with open(failure_file) as wf:
                    waivers_yaml.update(yaml.load(wf.read()))
            except IOError as e:
                logging.error('Error loading %s (%s).',
                              failure_file,
                              e.strerror)
                continue
            logging.info('Finished loading expected failure file: %s',
                         failure_file)
        return waivers_yaml

    def find_waivers(self, arch, board, bundle_abi, sdk_ver, first_api_level):
        """Finds waivers for the test board.

        @param arch: DUT's arch type.
        @param board: DUT's board name.
        @param bundle_abi: The test's abi type.
        @param sdk_ver: DUT's Android SDK version.
        @param first_api_level: DUT's Android first API level.
        @return a set of waivers/no-test-modules applied to the test board.
        """
        applied_waiver_list = set()
        for test, config in self.waivers_yaml.iteritems():
            if self._validate_waiver_config(arch, board, bundle_abi, sdk_ver,
                                            first_api_level, config):
                applied_waiver_list.add(test)
        logging.info('Excluding tests/packages from rerun: %s.',
                     applied_waiver_list)
        return applied_waiver_list

# Copyright (c) 2013 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.server.cros.network import wifi_cell_test_base

class network_WiFi_SimpleConnect(wifi_cell_test_base.WiFiCellTestBase):
    """Test that we can connect to router configured in various ways."""
    version = 1

    def parse_additional_arguments(self, commandline_args, additional_params):
        """Hook into super class to take control files parameters.

        @param commandline_args dict of parsed parameters from the autotest.
        @param additional_params list of tuple(HostapConfig,
                                               AssociationParameters).

        """
        self._configurations = additional_params


    def run_once(self):
        """Sets up a router, connects to it, pings it, and repeats."""
        client_mac = self.context.client.wifi_mac
        for router_conf, client_conf in self._configurations:
            self.context.configure(router_conf)
            self.context.capture_host.start_capture(router_conf.frequency,
                    width_type=router_conf.packet_capture_mode)
            client_conf.ssid = self.context.router.get_ssid()
            assoc_result = self.context.assert_connect_wifi(client_conf)
            if client_conf.expect_failure:
                logging.info('Skipping ping because we expected this '
                             'attempt to fail.')
            else:
                with self.context.client.assert_no_disconnects():
                    self.context.assert_ping_from_dut()
                self.context.client.shill.disconnect(client_conf.ssid)
                times_dict = {
                    'Discovery': assoc_result.discovery_time,
                    'Association': assoc_result.association_time,
                    'Configuration': assoc_result.configuration_time}
                for key in times_dict.keys():
                    self.output_perf_value(
                        description=key,
                        value=times_dict[key],
                        units='seconds',
                        higher_is_better=False,
                        graph=router_conf.perf_loggable_description)
            self.context.client.shill.delete_entries_for_ssid(client_conf.ssid)
            self.context.router.deconfig()
            self.context.capture_host.stop_capture()

# Copyright (c) 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib.cros.network import xmlrpc_datatypes
from autotest_lib.server.cros.network import hostap_config
from autotest_lib.server.cros.network import wifi_cell_test_base
import logging

class network_WiFi_RoamDbus(wifi_cell_test_base.WiFiCellTestBase):
    """Tests an intentional client-driven roam between APs

    This test seeks to associate the DUT with an AP with a set of
    association parameters, create a second AP with a second set of
    parameters but the same SSID, and send roam command to shill. After
    that shill will send a dbus roam command to wpa_supplicant. We seek
    to observe that the DUT successfully connects to the second AP in
    a reasonable amount of time.
    """

    version = 1
    TIMEOUT_SECONDS = 15

    def run_once(self,host):
        """Test body."""
        self._router0_conf = hostap_config.HostapConfig(channel=48,
                             mode=hostap_config.HostapConfig.MODE_11A)
        self._router1_conf = hostap_config.HostapConfig(channel=1)
        self._client_conf = xmlrpc_datatypes.AssociationParameters()

        # Configure the inital AP.
        self.context.configure(self._router0_conf)
        router_ssid = self.context.router.get_ssid()

        # Connect to the inital AP.
        self._client_conf.ssid = router_ssid
        self.context.assert_connect_wifi(self._client_conf)

        # Setup a second AP with the same SSID.
        self._router1_conf.ssid = router_ssid
        self.context.configure(self._router1_conf, multi_interface=True)

        # Get BSSIDs of the two APs
        bssid0 = self.context.router.get_hostapd_mac(0)
        bssid1 = self.context.router.get_hostapd_mac(1)

        # Wait for DUT to see the second AP
        self.context.client.wait_for_bss(bssid1)

        # Check which AP we are currently connected.
        # This is to include the case that wpa_supplicant
        # automatically roam to AP2 during the scan.
        interface = self.context.client.wifi_if
        current_bssid = self.context.client.iw_runner.get_current_bssid(interface)
        if current_bssid == bssid0:
            roam_to_bssid = bssid1
        else:
            roam_to_bssid = bssid0

        logging.info('Requesting roam from %s to %s', current_bssid, roam_to_bssid)
        # Send roam command to shill,
        # and shill will send dbus roam command to wpa_supplicant
        if not self.context.client.request_roam_dbus(roam_to_bssid, interface):
            raise error.TestFail('Failed to send roam command')

        # Expect that the DUT will re-connect to the new AP.
        if not self.context.client.wait_for_roam(
               roam_to_bssid, timeout_seconds=self.TIMEOUT_SECONDS):
            raise error.TestFail('Failed to roam.')
        self.context.router.deconfig()

# Copyright (c) 2013 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.client.common_lib import utils
from autotest_lib.client.common_lib.cros.network import xmlrpc_datatypes
from autotest_lib.server import test
from autotest_lib.server.cros.network import wifi_test_context_manager

class WiFiCellTestBase(test.test):
    """An abstract base class for autotests in WiFi cells.

    WiFiCell tests refer to participants in the test as client, router, and
    server.  The client is just the DUT and the router is a nearby AP which we
    configure in various ways to test the ability of the client to connect.
    There is a third entity called a server which is distinct from the autotest
    server.  In WiFiTests, the server is a host which the client can only talk
    to over the WiFi network.

    WiFiTests have a notion of the control network vs the WiFi network.  The
    control network refers to the network between the machine running the
    autotest server and the various machines involved in the test.  The WiFi
    network is the subnet(s) formed by WiFi routers between the server and the
    client.

    """

    @property
    def context(self):
        """@return the WiFi context for this test."""
        return self._wifi_context


    def parse_additional_arguments(self, commandline_args, additional_params):
        """Parse additional arguments for use in test.

        Subclasses should override this method do any other commandline parsing
        and setting grabbing that they need to do.  For test clarity, do not
        parse additional settings in the body of run_once.

        @param commandline_args dict of argument key, value pairs.
        @param additional_params object defined by test control file.

        """
        pass


    def warmup(self, host, raw_cmdline_args, additional_params=None,
            pcap_as_router=False):
        """
        Use the additional_params argument to pass in custom test data from
        control file to reuse test logic.  This object will be passed down via
        parse_additional_arguments.

        @param host host object representing the client DUT.
        @param raw_cmdline_args raw input from autotest.
        @param additional_params object passed in from control file.
        @param pcap_as_router True if the test requires the pcap to be
                configured as a router.

        """
        cmdline_args = utils.args_to_dict(raw_cmdline_args)
        logging.info('Running wifi test with commandline arguments: %r',
                     cmdline_args)
        self._wifi_context = wifi_test_context_manager.WiFiTestContextManager(
                self.__class__.__name__,
                host,
                cmdline_args,
                self.debugdir)

        self._wifi_context.setup(pcap_as_router=pcap_as_router)
        self.parse_additional_arguments(cmdline_args, additional_params)

        msg = '======= WiFi autotest setup complete. Starting test... ======='
        self._wifi_context.client.shill_debug_log(msg)


    def cleanup(self):
        msg = '======= WiFi autotest complete. Cleaning up... ======='
        self._wifi_context.client.shill_debug_log(msg)
        # If we fail during initialization, we might not have a context.
        if hasattr(self, '_wifi_context'):
            self._wifi_context.teardown()


    def configure_and_connect_to_ap(self, ap_config):
        """
        Configure the router as an AP with the given config and connect
        the DUT to it.

        @param ap_config HostapConfig object.

        @return name of the configured AP
        """
        self.context.configure(ap_config)
        ap_ssid = self.context.router.get_ssid()
        assoc_params = xmlrpc_datatypes.AssociationParameters(ssid=ap_ssid)
        self.context.assert_connect_wifi(assoc_params)
        return ap_ssid

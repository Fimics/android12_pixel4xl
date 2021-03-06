# Copyright 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Module contains a simple client lib to the devices RPC."""

import json
from six.moves import urllib

import common
from fake_device_server.client_lib import common_client
from fake_device_server import devices as s_devices


class DevicesClient(common_client.CommonClient):
    """Client library for devices method."""

    def __init__(self, *args, **kwargs):
        common_client.CommonClient.__init__(
                self, s_devices.DEVICES_PATH, *args, **kwargs)


    def get_device(self, device_id):
        """Returns info about the given |device_id|.

        @param device_id: valid device_id.
        """
        request = urllib.request.Request(self.get_url([device_id]),
                                         headers=self.add_auth_headers())
        url_h = urllib.request.urlopen(request)
        return json.loads(url_h.read())


    def list_devices(self):
        """Returns the list of the devices the server currently knows about."""
        request = urllib.request.Request(self.get_url(),
                                         headers=self.add_auth_headers())
        url_h = urllib.request.urlopen(request)
        return json.loads(url_h.read())


    def create_device(self, system_name, channel, **kwargs):
        """Creates a device using the args.

        @param system_name: name to give the system.
        @param channel: supported communication channel.
        @param kwargs: additional dictionary of args to put in config.
        """
        data = dict(name=system_name,
                    channel=channel,
                    **kwargs)
        headers = self.add_auth_headers({'Content-Type': 'application/json'})
        request = urllib.request.Request(self.get_url(), json.dumps(data),
                                         headers=headers)
        url_h = urllib.request.urlopen(request)
        return json.loads(url_h.read())

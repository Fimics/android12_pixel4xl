#!/usr/bin/env python3
#
#   Copyright 2018 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import collections
import json
import logging
import math
import os
import random
import re
import requests
import socket
import time

from urllib.parse import urlparse

from acts import utils
from acts.libs.proc import job


class DeviceOffline(Exception):
    """Exception if the device is no longer reachable via the network."""


class BaseLib():
    def __init__(self, addr, tc, client_id):
        self.address = addr
        self.test_counter = tc
        self.client_id = client_id

    def build_id(self, test_id):
        """Concatenates client_id and test_id to form a command_id.

        Args:
            test_id: string, unique identifier of test command.
        """
        return self.client_id + "." + str(test_id)

    def send_command(self, test_id, test_cmd, test_args, response_timeout=30):
        """Builds and sends a JSON command to SL4F server.

        Args:
            test_id: string, unique identifier of test command.
            test_cmd: string, sl4f method name of command.
            test_args: dictionary, arguments required to execute test_cmd.
            response_timeout: int, seconds to wait for a response before
                throwing an exception. Defaults to no timeout.

        Returns:
            Dictionary, Result of sl4f command executed.
        """
        if not utils.can_ping(job, urlparse(self.address).hostname):
            raise DeviceOffline("FuchsiaDevice %s is not reachable via the "
                                "network." % urlparse(self.address).hostname)
        test_data = json.dumps({
            "jsonrpc": "2.0",
            "id": test_id,
            "method": test_cmd,
            "params": test_args
        })
        try:
            return requests.get(url=self.address,
                                data=test_data,
                                timeout=response_timeout).json()
        except requests.exceptions.Timeout as e:
            if not utils.can_ping(job, urlparse(self.address).hostname):
                raise DeviceOffline(
                    "FuchsiaDevice %s is not reachable via the "
                    "network." % urlparse(self.address).hostname)
            else:
                logging.debug(
                    'FuchsiaDevice %s is online but SL4f call timed out.' %
                    urlparse(self.address).hostname)
                raise e

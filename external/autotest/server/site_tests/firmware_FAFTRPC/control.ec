# Copyright 2019 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from autotest_lib.server import utils

AUTHOR = "gredelston, kmshelton, waihong"
NAME = "firmware_FAFTRPC.ec"
PURPOSE = "Verify that the RPC system, and all EC RPCs, work as expected."
CRITERIA = "This test will fail if the EC system is not set up correctly."
ATTRIBUTES = "suite:faft_smoke"
TIME = "SHORT"
TEST_CATEGORY = "Functional"
TEST_CLASS = "firmware"
TEST_TYPE = "server"
JOB_RETRIES = 2

DOC = """
This test checks that all RPC functions on the EC subsystem are connected,
and that they roughly work as expected.

"""

args_dict = utils.args_to_dict(args)
servo_args = hosts.CrosHost.get_servo_arguments(args_dict)

def run_faftrpc(machine):
    host = hosts.create_host(machine, servo_args=servo_args)
    job.run_test("firmware_FAFTRPC",
                 host=host,
                 cmdline_args=args,
                 disable_sysinfo=True,
                 category_under_test="ec",
                 reboot_after_completion=True
                 )

parallel_simple(run_faftrpc, machines)

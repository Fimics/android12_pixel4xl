#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import acts_contrib.test_utils.power.PowerGnssBaseTest as GBT
from acts_contrib.test_utils.gnss import dut_log_test_utils as diaglog
from acts_contrib.test_utils.gnss import gnss_test_utils as gutil
import time
import os
from acts import utils
MDLOG_RUNNING_TIME = 1200
DUT_ACTION_WAIT_TIME = 2

class PowerGnssDpoSimTest(GBT.PowerGnssBaseTest):
    """Power baseline tests for rockbottom state.
    Rockbottom for GNSS on/off, screen on/off, everything else turned off

    """

    def measure_gnsspower_test_func(self):
        """Test function for baseline rockbottom tests.

        Decode the test config from the test name, set device to desired state.
        Measure power and plot results.
        """
        result = self.collect_power_data()
        self.pass_fail_check(result.average_current)

    # Test cases
    def test_gnss_dpoOFF_measurement(self):
        utils.set_location_service(self.dut, True)
        time.sleep(DUT_ACTION_WAIT_TIME)
        self.dut.reboot()
        gutil.write_modemconfig(self.dut, self.mdsapp,
                                self.dpooff_nv_dict, self.modemparfile)
        self.dut.reboot()
        gutil.verify_modemconfig(self.dut, self.dpooff_nv_dict, self.modemparfile)
        gutil.clear_aiding_data_by_gtw_gpstool(self.dut)
        gutil.start_gnss_by_gtw_gpstool(self.dut, state=True, type="gnss",
                                        bgdisplay=True)
        time.sleep(DUT_ACTION_WAIT_TIME)
        diaglog.start_diagmdlog_background(self.dut, maskfile=self.maskfile)
        self.disconnect_usb(self.dut, MDLOG_RUNNING_TIME)
        qxdm_log_path = os.path.join(self.log_path, 'QXDM')
        diaglog.stop_background_diagmdlog(self.dut, qxdm_log_path, keep_logs=False)
        self.measure_gnsspower_test_func()
        gutil.start_gnss_by_gtw_gpstool(self.dut, state=False)
        gps_log_path = os.path.join(self.log_path, 'GPS_LOGS')
        diaglog.get_gpstool_logs(self.dut, gps_log_path, keep_logs=False)

    def test_gnss_dpoON_measurement(self):
        utils.set_location_service(self.dut, True)
        time.sleep(DUT_ACTION_WAIT_TIME)
        self.dut.reboot()
        gutil.write_modemconfig(self.dut, self.mdsapp,
                                self.dpoon_nv_dict, self.modemparfile)
        self.dut.reboot()
        gutil.verify_modemconfig(self.dut, self.dpoon_nv_dict, self.modemparfile)
        gutil.clear_aiding_data_by_gtw_gpstool(self.dut)
        gutil.start_gnss_by_gtw_gpstool(self.dut, state=True,type="gnss",
                                        bgdisplay=True)
        time.sleep(DUT_ACTION_WAIT_TIME)
        diaglog.start_diagmdlog_background(self.dut, maskfile=self.maskfile)
        self.disconnect_usb(self.dut, MDLOG_RUNNING_TIME)
        qxdm_log_path = os.path.join(self.log_path, 'QXDM')
        diaglog.stop_background_diagmdlog(self.dut, qxdm_log_path, keep_logs=False)

        self.measure_gnsspower_test_func()
        gutil.start_gnss_by_gtw_gpstool(self.dut, state=False)
        gps_log_path = os.path.join(self.log_path, 'GPS_LOGS')
        diaglog.get_gpstool_logs(self.dut, gps_log_path, keep_logs=False)

    def test_gnss_rockbottom(self):
        self.dut.send_keycode("SLEEP")
        time.sleep(120)
        self.measure_gnsspower_test_func()

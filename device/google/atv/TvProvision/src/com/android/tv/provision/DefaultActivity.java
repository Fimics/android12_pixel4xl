/*
 * Copyright (C) 2018 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.android.tv.provision;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.pm.PackageManager;
import android.net.wifi.WifiManager;
import android.net.wifi.WifiConfiguration;
import android.os.Bundle;
import android.os.SystemProperties;
import android.os.UserHandle;
import android.os.UserManager;
import android.provider.Settings;
import android.util.Log;

/**
 * Application that sets the provisioned bit, like SetupWizard does.
 */
public class DefaultActivity extends Activity {

    private static final String TV_USER_SETUP_COMPLETE = "tv_user_setup_complete";
    private static final String TAG = "TvProvision";
    private static final int ADD_NETWORK_FAIL = -1;
    @Override
    protected void onCreate(Bundle icicle) {
        super.onCreate(icicle);

        // Add a persistent setting to allow other apps to know the device has been provisioned.
        if (!isRestrictedUser()) {
            Settings.Global.putInt(getContentResolver(), Settings.Global.DEVICE_PROVISIONED, 1);
        }
        Settings.Secure.putInt(getContentResolver(), Settings.Secure.USER_SETUP_COMPLETE, 1);
        Settings.Secure.putInt(getContentResolver(), TV_USER_SETUP_COMPLETE, 1);
        if (SystemProperties.get("ro.boot.qemu").equals("1")) {
          // Emulator-only: Enable USB debugging and adb
          Settings.Global.putInt(getContentResolver(), Settings.Global.ADB_ENABLED, 1);
          // Add network with SSID "AndroidWifi"
          WifiConfiguration config = new WifiConfiguration();
          config.SSID = "\"AndroidWifi\"";
          config.setSecurityParams(WifiConfiguration.SECURITY_TYPE_OPEN);
          WifiManager mWifiManager = getApplicationContext().getSystemService(WifiManager.class);
          int netId = mWifiManager.addNetwork(config);
          if (netId == ADD_NETWORK_FAIL || mWifiManager.enableNetwork(netId, true)) {
              Log.e(TAG, "Unable to add Wi-Fi network AndroidWifi.");
          }
        }

        // remove this activity from the package manager.
        PackageManager pm = getPackageManager();
        ComponentName name = new ComponentName(this, DefaultActivity.class);
        pm.setComponentEnabledSetting(name, PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP);

        // terminate the activity.
        finish();
    }

    private boolean isRestrictedUser() {
        UserManager userManager = (UserManager) getSystemService(Context.USER_SERVICE);
        return userManager.isRestrictedProfile();
    }
}


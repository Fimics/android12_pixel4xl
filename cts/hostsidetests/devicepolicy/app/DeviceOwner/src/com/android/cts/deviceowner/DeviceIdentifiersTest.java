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
package com.android.cts.deviceowner;

import android.platform.test.annotations.AsbSecurityTest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.telephony.SubscriptionInfo;
import android.telephony.SubscriptionManager;
import android.telephony.TelephonyManager;

import com.android.compatibility.common.util.ShellIdentityUtils;

/**
 * Verifies device identifier access for the device owner.
 */
public class DeviceIdentifiersTest extends BaseDeviceOwnerTest {

    private static final String DEVICE_ID_WITH_PERMISSION_ERROR_MESSAGE =
            "An unexpected value was received by the device owner with the READ_PHONE_STATE "
                    + "permission when invoking %s";

    @AsbSecurityTest(cveBugId = 173421434)
    public void testDeviceOwnerCanGetDeviceIdentifiersWithPermission() {
        // The device owner with the READ_PHONE_STATE permission should have access to all device
        // identifiers. However since the TelephonyManager methods can return null this method
        // verifies that the device owner with the READ_PHONE_STATE permission receives the same
        // value that the shell identity receives with the READ_PRIVILEGED_PHONE_STATE permission.
        TelephonyManager telephonyManager = (TelephonyManager) mContext.getSystemService(
                Context.TELEPHONY_SERVICE);
        try {
            assertEquals(String.format(DEVICE_ID_WITH_PERMISSION_ERROR_MESSAGE, "getDeviceId"),
                    ShellIdentityUtils.invokeMethodWithShellPermissions(telephonyManager,
                            TelephonyManager::getDeviceId), telephonyManager.getDeviceId());
            assertEquals(String.format(DEVICE_ID_WITH_PERMISSION_ERROR_MESSAGE, "getImei"),
                    ShellIdentityUtils.invokeMethodWithShellPermissions(telephonyManager,
                            TelephonyManager::getImei), telephonyManager.getImei());
            assertEquals(String.format(DEVICE_ID_WITH_PERMISSION_ERROR_MESSAGE, "getMeid"),
                    ShellIdentityUtils.invokeMethodWithShellPermissions(telephonyManager,
                            TelephonyManager::getMeid), telephonyManager.getMeid());
            assertEquals(String.format(DEVICE_ID_WITH_PERMISSION_ERROR_MESSAGE, "getSubscriberId"),
                    ShellIdentityUtils.invokeMethodWithShellPermissions(telephonyManager,
                            TelephonyManager::getSubscriberId), telephonyManager.getSubscriberId());
            assertEquals(
                    String.format(DEVICE_ID_WITH_PERMISSION_ERROR_MESSAGE, "getSimSerialNumber"),
                    ShellIdentityUtils.invokeMethodWithShellPermissions(telephonyManager,
                            TelephonyManager::getSimSerialNumber),
                    telephonyManager.getSimSerialNumber());
            assertEquals(
                    String.format(DEVICE_ID_WITH_PERMISSION_ERROR_MESSAGE, "getNai"),
                    ShellIdentityUtils.invokeMethodWithShellPermissions(telephonyManager,
                            TelephonyManager::getNai), telephonyManager.getNai());
            assertEquals(String.format(DEVICE_ID_WITH_PERMISSION_ERROR_MESSAGE, "Build#getSerial"),
                    ShellIdentityUtils.invokeStaticMethodWithShellPermissions(Build::getSerial),
                    Build.getSerial());
            SubscriptionManager subscriptionManager =
                    (SubscriptionManager) mContext.getSystemService(
                            Context.TELEPHONY_SUBSCRIPTION_SERVICE);
            int subId = subscriptionManager.getDefaultSubscriptionId();
            if (subId != SubscriptionManager.INVALID_SUBSCRIPTION_ID) {
                SubscriptionInfo expectedSubInfo =
                        ShellIdentityUtils.invokeMethodWithShellPermissions(subscriptionManager,
                                (sm) -> sm.getActiveSubscriptionInfo(subId));
                SubscriptionInfo actualSubInfo = subscriptionManager.getActiveSubscriptionInfo(
                        subId);
                assertEquals(String.format(DEVICE_ID_WITH_PERMISSION_ERROR_MESSAGE, "getIccId"),
                        expectedSubInfo.getIccId(), actualSubInfo.getIccId());
            }
        } catch (SecurityException e) {
            fail("The device owner with the READ_PHONE_STATE permission must be able to access "
                    + "the device IDs: " + e);
        }
    }
}

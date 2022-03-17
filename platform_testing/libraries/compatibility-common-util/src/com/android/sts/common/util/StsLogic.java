/*
 * Copyright (C) 2021 The Android Open Source Project
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

package com.android.sts.common.util;

import static org.junit.Assume.*;

import android.platform.test.annotations.AsbSecurityTest;

import com.android.compatibility.common.util.BusinessLogicMapStore;
import com.android.compatibility.common.util.MultiLog;

import org.junit.runner.Description;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/** Common STS extra business logic for host-side and device-side to implement. */
public interface StsLogic extends MultiLog {

    static final String LOG_TAG = StsLogic.class.getSimpleName();

    // keep in sync with google3:
    // //wireless/android/partner/apbs/*/config/xtsbgusinesslogic/sts_business_logic.gcl
    List<String> STS_EXTRA_BUSINESS_LOGIC_FULL = Arrays.asList(new String[]{
        "uploadSpl",
        "uploadModificationTime",
    });
    List<String> STS_EXTRA_BUSINESS_LOGIC_INCREMENTAL = Arrays.asList(new String[]{
        "uploadSpl",
        "uploadModificationTime",
        "incremental",
    });

    Description getTestDescription();

    LocalDate getDeviceSpl();

    default long[] getCveBugIds() {
        AsbSecurityTest annotation = getTestDescription().getAnnotation(AsbSecurityTest.class);
        if (annotation == null) {
            return null;
        }
        return annotation.cveBugId();
    }

    default LocalDate getMinTestSpl() {
        Map<String, String> map = BusinessLogicMapStore.getMap("security_bulletins");
        if (map == null) {
            throw new IllegalArgumentException("Could not find the security bulletin map");
        }
        LocalDate minSpl = null;
        for (long cveBugId : getCveBugIds()) {
            String splString = map.get(Long.toString(cveBugId));
            if (splString == null) {
                // This bug id wasn't found in the map.
                // This is a new test or the bug was removed from the bulletin and this is an old
                // binary. Neither is a critical issue and the test will run in these cases.
                // New test: developer should be able to write the test without getting blocked.
                // Removed bug + old binary: test will run.
                logInfo(LOG_TAG, "could not find the CVE bug %d in the spl map", cveBugId);
                continue;
            }
            LocalDate spl = SplUtils.localDateFromSplString(splString);
            if (minSpl == null) {
                minSpl = spl;
            } else if (spl.isBefore(minSpl)) {
                minSpl = spl;
            }
        }
        return minSpl;
    }

    default LocalDate getMinModificationDate() {
        Map<String, String> map = BusinessLogicMapStore.getMap("sts_modification_times");
        if (map == null) {
            throw new IllegalArgumentException("Could not find the modification date map");
        }
        LocalDate minModificationDate = null;
        for (long cveBugId : getCveBugIds()) {
            String modificationMillisString = map.get(Long.toString(cveBugId));
            if (modificationMillisString == null) {
                logInfo(LOG_TAG,
                        "Could not find the CVE bug %d in the modification date map", cveBugId);
                continue;
            }
            LocalDate modificationDate =
                    SplUtils.localDateFromMillis(Long.parseLong(modificationMillisString));
            if (minModificationDate == null) {
                minModificationDate = modificationDate;
            } else if (modificationDate.isBefore(minModificationDate)) {
                minModificationDate = modificationDate;
            }
        }
        return minModificationDate;
    }

    default boolean shouldSkipIncremental() {
        logDebug(LOG_TAG, "filtering by incremental");

        long[] bugIds = getCveBugIds();
        if (bugIds == null) {
            // There were no @AsbSecurityTest annotations
            logInfo(LOG_TAG, "not an ASB test");
            return false;
        }

        // check if test spl is older than the past 6 months from the device spl
        LocalDate deviceSpl = getDeviceSpl();
        LocalDate incrementalCutoffSpl = deviceSpl.plusMonths(-6);

        LocalDate minTestModifiedDate = getMinModificationDate();
        if (minTestModifiedDate == null) {
            // could not get the modification date - run the test
            if (Arrays.stream(bugIds).min().getAsLong() < 157905780) {
                // skip if the bug id is older than ~ June 2020
                // otherwise the test will run due to missing data
                logDebug(LOG_TAG, "no data for this old test");
                return true;
            }
          return false;
        }
        if (minTestModifiedDate.isAfter(incrementalCutoffSpl)) {
            logDebug(LOG_TAG, "the test was recently modified");
            return false;
        }

        LocalDate minTestSpl = getMinTestSpl();
        if (minTestSpl == null) {
            // could not get the test spl - run the test
            logWarn(LOG_TAG, "could not get the test SPL");
            return false;
        }
        if (minTestSpl.isAfter(incrementalCutoffSpl)) {
            logDebug(LOG_TAG, "the test has a recent SPL");
            return false;
        }

        logDebug(LOG_TAG, "test should skip");
        return true;
    }

    default boolean shouldSkipSpl() {
        return true;
    }

    default void skip(String message) {
        assumeTrue(message, false);
    }
}

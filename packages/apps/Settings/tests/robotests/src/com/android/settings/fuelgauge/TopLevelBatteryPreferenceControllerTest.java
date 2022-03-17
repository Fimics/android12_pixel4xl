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

package com.android.settings.fuelgauge;

import static com.android.settings.core.BasePreferenceController.AVAILABLE;
import static com.android.settings.core.BasePreferenceController.UNSUPPORTED_ON_DEVICE;

import static com.google.common.truth.Truth.assertThat;

import static org.mockito.Mockito.any;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;

import androidx.preference.Preference;

import com.android.settings.R;
import com.android.settings.testutils.FakeFeatureFactory;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.MockitoAnnotations;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
public class TopLevelBatteryPreferenceControllerTest {
    private Context mContext;
    private FakeFeatureFactory mFeatureFactory;
    private TopLevelBatteryPreferenceController mController;
    private BatterySettingsFeatureProvider mBatterySettingsFeatureProvider;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        mFeatureFactory = FakeFeatureFactory.setupForTest();
        mContext = spy(Robolectric.setupActivity(Activity.class));
        mController = new TopLevelBatteryPreferenceController(mContext, "test_key");
        mBatterySettingsFeatureProvider =
                mFeatureFactory.batterySettingsFeatureProvider;
    }

    @After
    public void cleanUp() {
        TopLevelBatteryPreferenceController.sReplacingActivityMap.clear();
    }

    @Test
    public void getAvailibilityStatus_availableByDefault() {
        assertThat(mController.getAvailabilityStatus()).isEqualTo(AVAILABLE);
    }

    @Test
    @Config(qualifiers = "mcc999")
    public void getAvailabilityStatus_unsupportedWhenSet() {
        assertThat(mController.getAvailabilityStatus()).isEqualTo(UNSUPPORTED_ON_DEVICE);
    }

    @Test
    public void handlePreferenceTreeClick_noFragment_noCustomActivityCalled() {
        Preference preference = new Preference(mContext);

        assertThat(mController.handlePreferenceTreeClick(preference)).isFalse();
    }

    @Test
    public void handlePreferenceTreeClick_sameActivityReturned_noCustomActivityCalled() {
        String fragmentPath = "my.fragment.ClassName";
        Preference preference = mock(Preference.class);
        when(preference.getFragment()).thenReturn(fragmentPath);
        ComponentName pathName = mController.convertClassPathToComponentName(fragmentPath);
        when(mBatterySettingsFeatureProvider.getReplacingActivity(any())).thenReturn(pathName);

        assertThat(mController.handlePreferenceTreeClick(preference)).isFalse();
    }

    @Test
    public void handlePreferenceTreeClick_newActivityReturned_newActivityRedirected() {
        String fragmentPath = "my.fragment.ClassName";
        Preference preference = mock(Preference.class);
        when(preference.getFragment()).thenReturn(fragmentPath);
        String newFragmentPath = "my.fragment.NewClassName";
        ComponentName newPathName = mController.convertClassPathToComponentName(newFragmentPath);
        when(mBatterySettingsFeatureProvider.getReplacingActivity(any())).thenReturn(
                newPathName);
        doNothing().when(mContext).startActivity(any());

        assertThat(mController.handlePreferenceTreeClick(preference)).isTrue();
    }

    @Test
    public void handlePreferenceTreeClick_calledMultipleTimes_fetchedFromCache() {
        String fragmentPath = "my.fragment.ClassName";
        Preference preference = mock(Preference.class);
        when(preference.getFragment()).thenReturn(fragmentPath);
        String newFragmentPath = "my.fragment.NewClassName";
        ComponentName newPathName = mController.convertClassPathToComponentName(newFragmentPath);
        when(mBatterySettingsFeatureProvider.getReplacingActivity(any())).thenReturn(
                newPathName);
        doNothing().when(mContext).startActivity(any());

        assertThat(mController.handlePreferenceTreeClick(preference)).isTrue();
        assertThat(mController.handlePreferenceTreeClick(preference)).isTrue();
        verify(mBatterySettingsFeatureProvider, times(1)).getReplacingActivity(any());
    }

    @Test
    public void convertClassPathToComponentName_nullInput_returnsNull() {
        assertThat(mController.convertClassPathToComponentName(null)).isNull();
    }

    @Test
    public void convertClassPathToComponentName_emptyStringInput_returnsNull() {
        assertThat(mController.convertClassPathToComponentName("")).isNull();
    }

    @Test
    public void convertClassPathToComponentName_singleClassName_returnsCorrectComponentName() {
        ComponentName output = mController.convertClassPathToComponentName("ClassName");

        assertThat(output.getPackageName()).isEqualTo("");
        assertThat(output.getClassName()).isEqualTo("ClassName");
    }

    @Test
    public void convertClassPathToComponentName_validAddress_returnsCorrectComponentName() {
        ComponentName output = mController.convertClassPathToComponentName("my.fragment.ClassName");

        assertThat(output.getPackageName()).isEqualTo("my.fragment");
        assertThat(output.getClassName()).isEqualTo("ClassName");
    }

    @Test
    public void getDashboardLabel_returnsCorrectLabel() {
        BatteryInfo info = new BatteryInfo();
        info.batteryPercentString = "3%";
        assertThat(mController.getDashboardLabel(mContext, info, true))
                .isEqualTo(info.batteryPercentString);

        info.remainingLabel = "Phone will shut down soon";
        assertThat(mController.getDashboardLabel(mContext, info, true))
                .isEqualTo("3% - Phone will shut down soon");

        info.discharging = false;
        info.chargeLabel = "5% - charging";
        assertThat(mController.getDashboardLabel(mContext, info, true)).isEqualTo("5% - charging");
    }

    @Test
    public void getSummary_batteryNotPresent_shouldShowWarningMessage() {
        mController.mIsBatteryPresent = false;

        assertThat(mController.getSummary())
                .isEqualTo(mContext.getString(R.string.battery_missing_message));
    }
}

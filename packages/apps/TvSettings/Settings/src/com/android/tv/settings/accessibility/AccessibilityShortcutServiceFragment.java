/*
 * Copyright (C) 2017 The Android Open Source Project
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

package com.android.tv.settings.accessibility;

import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.tvsettings.TvSettingsEnums;
import android.content.ComponentName;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.provider.Settings;
import android.text.TextUtils;
import android.view.accessibility.AccessibilityManager;

import androidx.annotation.Keep;
import androidx.fragment.app.Fragment;
import androidx.leanback.preference.LeanbackSettingsFragmentCompat;
import androidx.preference.Preference;
import androidx.preference.PreferenceScreen;

import com.android.tv.settings.R;
import com.android.tv.settings.RadioPreference;
import com.android.tv.settings.SettingsPreferenceFragment;
import com.android.tv.twopanelsettings.TwoPanelSettingsFragment;

import java.util.List;

/**
 * Fragment imitating a single-selection list for picking the accessibility shortcut service
 */
@Keep
public class AccessibilityShortcutServiceFragment extends SettingsPreferenceFragment implements
        AccessibilityServiceConfirmationFragment.OnAccessibilityServiceConfirmedListener {
    private static final String SERVICE_RADIO_GROUP = "service_group";

    private final Preference.OnPreferenceChangeListener mPreferenceChangeListener =
            (preference, newValue) -> {
                final String newCompString = preference.getKey();
                final String currentService =
                        AccessibilityShortcutFragment.getCurrentService(getContext());
                if ((Boolean) newValue && !TextUtils.equals(newCompString, currentService)) {
                    final ComponentName cn = ComponentName.unflattenFromString(newCompString);
                    final CharSequence label = preference.getTitle();
                    final Fragment confirmFragment =
                            AccessibilityServiceConfirmationFragment.newInstance(cn, label, true);
                    confirmFragment.setTargetFragment(AccessibilityShortcutServiceFragment.this, 0);

                    final Fragment settingsFragment = getCallbackFragment();
                    if (settingsFragment instanceof LeanbackSettingsFragmentCompat) {
                        ((LeanbackSettingsFragmentCompat) settingsFragment)
                                .startImmersiveFragment(confirmFragment);
                    } else if (settingsFragment instanceof TwoPanelSettingsFragment) {
                        ((TwoPanelSettingsFragment) settingsFragment)
                                .startImmersiveFragment(confirmFragment);
                    } else {
                        throw new IllegalStateException("Not attached to settings fragment??");
                    }
                }
                return false;
            };

    @Override
    public void onCreatePreferences(Bundle savedInstanceState, String rootKey) {
        setPreferencesFromResource(R.xml.accessibility_shortcut_service, null);

        final PreferenceScreen screen = getPreferenceScreen();
        final Context themedContext = getPreferenceManager().getContext();

        final List<AccessibilityServiceInfo> installedServices = getContext()
                .getSystemService(AccessibilityManager.class)
                .getInstalledAccessibilityServiceList();
        final PackageManager packageManager = getContext().getPackageManager();
        final String currentService = AccessibilityShortcutFragment.getCurrentService(getContext());
        for (AccessibilityServiceInfo service : installedServices) {
            final RadioPreference preference = new RadioPreference(themedContext);
            preference.setPersistent(false);
            preference.setRadioGroup(SERVICE_RADIO_GROUP);
            preference.setOnPreferenceChangeListener(mPreferenceChangeListener);

            final String serviceString = service.getComponentName().flattenToString();
            if (TextUtils.equals(currentService, serviceString)) {
                preference.setChecked(true);
            }
            preference.setKey(serviceString);
            preference.setTitle(service.getResolveInfo().loadLabel(packageManager));

            screen.addPreference(preference);
        }
    }

    @Override
    public void onAccessibilityServiceConfirmed(ComponentName componentName, boolean enabling) {
        final String componentString = componentName.flattenToString();
        Settings.Secure.putString(getContext().getContentResolver(),
                Settings.Secure.ACCESSIBILITY_SHORTCUT_TARGET_SERVICE,
                componentString);

        if (!(getCallbackFragment() instanceof TwoPanelSettingsFragment)) {
            getFragmentManager().popBackStack();
        }

        if (enabling) {
            // the listener is only triggered when enabling a new service
            int prefCount = getPreferenceScreen().getPreferenceCount();
            for (int i = 0; i < prefCount; i++) {
                RadioPreference pref = (RadioPreference) getPreferenceScreen().getPreference(i);
                boolean shouldEnable = componentString.equals(pref.getKey());
                if (pref != null) {
                    pref.setChecked(shouldEnable);
                }
            }
        }
    }

    @Override
    protected int getPageId() {
        return TvSettingsEnums.SYSTEM_A11Y_SHORTCUT_SERVICE;
    }
}

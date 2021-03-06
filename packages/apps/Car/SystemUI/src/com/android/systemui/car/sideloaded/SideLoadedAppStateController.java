/*
 * Copyright (C) 2020 The Android Open Source Project
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

package com.android.systemui.car.sideloaded;

import android.util.Log;
import android.view.Display;

import com.android.systemui.dagger.SysUISingleton;

import javax.inject.Inject;

/**
 * Manager responsible for displaying proper UI when an unsafe app is detected.
 */
@SysUISingleton
public class SideLoadedAppStateController {
    private static final String TAG = SideLoadedAppStateController.class.getSimpleName();

    @Inject
    SideLoadedAppStateController() {
    }

    void onUnsafeInstalledAppsDetected() {
        Log.d(TAG, "Unsafe installed apps detected.");
    }

    void onUnsafeTaskCreatedOnDisplay(Display display) {
        Log.d(TAG, "Unsafe task created on display " + display.getDisplayId() + ".");
    }

    void onSafeTaskDisplayedOnDisplay(Display display) {
        Log.d(TAG, "Safe task displayed on display " + display.getDisplayId() + ".");
    }

    void onUnsafeTaskDisplayedOnDisplay(Display display) {
        Log.d(TAG, "Unsafe task displayed on display " + display.getDisplayId() + ".");
    }
}

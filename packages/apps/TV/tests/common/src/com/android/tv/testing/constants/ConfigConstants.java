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
 * limitations under the License
 */

package com.android.tv.testing.constants;

import android.os.Build;

/** Constants for Robolectic Config. */
public final class ConfigConstants {

    public static final String MANIFEST = "vendor/unbundled_google/packages/TV/AndroidManifest.xml";
    public static final int SDK = Build.VERSION_CODES.M;
    public static final int MIN_SDK = Build.VERSION_CODES.M;
    public static final int MAX_SDK = Build.VERSION_CODES.P;

    private ConfigConstants() {}
}

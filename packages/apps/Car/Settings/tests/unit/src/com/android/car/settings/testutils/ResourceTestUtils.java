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

package com.android.car.settings.testutils;

import android.content.Context;

public class ResourceTestUtils {
    /**
     * Retrieve a resource string from the current package based on a name identifier.
     */
    public static String getString(Context context, String name) {
        return context.getResources().getString(context.getResources().getIdentifier(
                name, /* type= */ "string", context.getPackageName()));
    }

    /**
     * Retrieve a formatted resource string from the current package based on a name identifier,
     * substituting the format arguments as defined in {@link java.util.Formatter} and
     * {@link java.lang.String#format}.
     */
    public static String getString(Context context, String name, Object... formatArgs) {
        return context.getResources().getString(context.getResources().getIdentifier(
                name, /* type= */ "string", context.getPackageName()), formatArgs);
    }
}

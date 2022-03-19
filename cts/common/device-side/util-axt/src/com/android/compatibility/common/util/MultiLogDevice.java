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

package com.android.compatibility.common.util;

import android.util.Log;
import com.android.compatibility.common.util.MultiLog;

/** Implement the deviceside interface for logging on host+device-common code. */
public interface MultiLogDevice extends MultiLog {
    /** {@inheritDoc} */
    @Override
    default void logInfo(String logTag, String format, Object... args) {
        Log.i(logTag, String.format(format, args));
    }

    /** {@inheritDoc} */
    @Override
    default void logDebug(String logTag, String format, Object... args) {
        Log.d(logTag, String.format(format, args));
    }

    /** {@inheritDoc} */
    @Override
    default void logWarn(String logTag, String format, Object... args) {
        Log.w(logTag, String.format(format, args));
    }

    /** {@inheritDoc} */
    @Override
    default void logError(String logTag, String format, Object... args) {
        Log.e(logTag, String.format(format, args));
    }
}

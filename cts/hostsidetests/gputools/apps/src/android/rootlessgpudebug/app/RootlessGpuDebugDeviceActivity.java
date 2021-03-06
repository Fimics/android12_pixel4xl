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

package android.rootlessgpudebug.app;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;

import java.lang.Override;

public class RootlessGpuDebugDeviceActivity extends Activity {

    static {
        System.loadLibrary("ctsgputools_jni");
    }

    private static final String TAG = RootlessGpuDebugDeviceActivity.class.getSimpleName();

    @Override
    public void onCreate(Bundle icicle) {
        super.onCreate(icicle);

        String result = nativeInitVulkan();
        Log.i(TAG, result);

        result = nativeInitGLES();
        Log.i(TAG, result);

        Log.i(TAG, "RootlessGpuDebug activity complete");
    }

    private static native String nativeInitVulkan();
    private static native String nativeInitGLES();

}


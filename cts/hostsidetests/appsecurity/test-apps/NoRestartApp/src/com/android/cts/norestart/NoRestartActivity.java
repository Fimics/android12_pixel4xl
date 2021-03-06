/*
 * Copyright (C) 2016 The Android Open Source Project
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

package com.android.cts.norestart;

import android.app.Activity;
import android.content.Intent;
import android.content.res.Resources;
import android.os.Bundle;

public class NoRestartActivity extends Activity {
    private final static String RESOURCE_ID =
            "com.android.cts.norestart.feature:string/no_restart_feature_text";

    private int mCreateCount;
    private int mNewIntentCount;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.no_restart_activity);
        mCreateCount++;
        sendBroadcast();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        mNewIntentCount++;
        sendBroadcast();
    }

    private void sendBroadcast() {
        final Intent intent = new Intent("com.android.cts.norestart.BROADCAST");
        intent.putExtra("CREATE_COUNT", mCreateCount);
        intent.putExtra("NEW_INTENT_COUNT", mNewIntentCount);
        intent.putExtra("RESOURCE_CONTENT", getResourceInFeature());
        sendBroadcast(intent);
    }

    private String getResourceInFeature() {
        final Resources res = getResources();
        final int resId = res.getIdentifier(RESOURCE_ID, null, null);
        if (resId == 0) {
            return null;
        }
        return res.getString(resId);
    }
}

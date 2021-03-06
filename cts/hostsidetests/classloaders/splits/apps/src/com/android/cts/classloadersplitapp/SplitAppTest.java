/*
 * Copyright (C) 2014 The Android Open Source Project
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

package com.android.cts.classloadersplitapp;

import static org.hamcrest.CoreMatchers.*;
import static org.junit.Assert.*;

import android.app.Activity;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;

import androidx.test.InstrumentationRegistry;
import androidx.test.rule.ActivityTestRule;
import androidx.test.rule.ServiceTestRule;
import androidx.test.runner.AndroidJUnit4;

import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TestRule;
import org.junit.runner.Description;
import org.junit.runner.RunWith;
import org.junit.runners.model.Statement;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

@RunWith(AndroidJUnit4.class)
public class SplitAppTest {
    /* The feature hierarchy looks like this:

        APK_BASE (PathClassLoader)
          ^
          |
        APK_FEATURE_A (DelegateLastClassLoader)
          ^
          |
        APK_FEATURE_B (PathClassLoader)

     */

    private static final String PACKAGE = "com.android.cts.classloadersplitapp";
    private static final ComponentName FEATURE_A_ACTIVITY =
            ComponentName.createRelative(PACKAGE, ".feature_a.FeatureAActivity");
    private static final ComponentName FEATURE_B_ACTIVITY =
            ComponentName.createRelative(PACKAGE, ".feature_b.FeatureBActivity");
    private static final ComponentName FEATURE_A_SERVICE =
            ComponentName.createRelative(PACKAGE, ".feature_a.FeatureAService");
    private static final ComponentName FEATURE_B_SERVICE =
            ComponentName.createRelative(PACKAGE, ".feature_b.FeatureBService");

    @Rule
    public ActivityTestRule<BaseActivity> mBaseActivityRule =
            new ActivityTestRule<>(BaseActivity.class);

    // Do not launch this activity lazily. We use this rule to launch all feature Activities,
    // so we use #launchActivity() with the correct Intent.
    @Rule
    public ActivityTestRule<Activity> mFeatureActivityRule =
            new ActivityTestRule<>(Activity.class, true /*initialTouchMode*/,
                    false /*launchActivity*/);

    @Rule
    public AppContextTestRule mAppContextTestRule = new AppContextTestRule();

    @Rule
    public ServiceTestRule mServiceTestRule = new ServiceTestRule();

    @Test
    public void testBaseClassLoader() throws Exception {
        final Context context = mBaseActivityRule.getActivity();
        assertEquals("dalvik.system.PathClassLoader",
            context.getClassLoader().getClass().getName());
    }

    @Test
    public void testFeatureAClassLoader() throws Exception {
        final Context context = mFeatureActivityRule.launchActivity(
                new Intent().setComponent(FEATURE_A_ACTIVITY));

        // Feature A requests a DelegateLastClassLoader, so make sure
        // it is given one.
        final ClassLoader cl = context.getClassLoader();
        assertEquals("dalvik.system.DelegateLastClassLoader", cl.getClass().getName());

        // Also assert that its parent (the base) is a PathClassLoader.
        assertEquals("dalvik.system.PathClassLoader", cl.getParent().getClass().getName());
    }

    @Test
    public void testFeatureBClassLoader() throws Exception {
        // Feature B depends on A, so we expect both to be available.
        final Context context = mFeatureActivityRule.launchActivity(
                new Intent().setComponent(FEATURE_B_ACTIVITY));

        // Feature B requests a PathClassLoader but it depends on feature A, which
        // requests a DelegateLastClassLoader.
        final ClassLoader cl = context.getClassLoader();
        assertEquals("dalvik.system.PathClassLoader", cl.getClass().getName());
        assertEquals("dalvik.system.DelegateLastClassLoader", cl.getParent().getClass().getName());
    }

    @Test
    public void testAllReceivers() throws Exception {
        final Context context = mAppContextTestRule.getContext();
        final ExtrasResultReceiver receiver = sendOrderedBroadcast(context);
        final Bundle results = receiver.get();

        // Base.
        assertThat(results.getString("loaderClassName"),
            equalTo("dalvik.system.PathClassLoader"));

        // Feature A.
        assertThat(results.getString("featureA_loaderClassName"),
            equalTo("dalvik.system.DelegateLastClassLoader"));
        assertThat(results.getString("featureA_parentClassName"),
            equalTo("dalvik.system.PathClassLoader"));

        // Feature B.
        assertThat(results.getString("featureB_loaderClassName"),
            equalTo("dalvik.system.PathClassLoader"));
        assertThat(results.getString("featureB_parentClassName"),
            equalTo("dalvik.system.DelegateLastClassLoader"));
    }

    @Test
    public void testBaseServiceClassLoader() throws Exception {
        final Service service = getService(new ComponentName(mAppContextTestRule.getContext(),
                BaseService.class));
        assertThat(service.getClassLoader().getClass().getName(),
                equalTo("dalvik.system.PathClassLoader"));
    }

    @Test
    public void testFeatureAServiceClassLoader() throws Exception {
        final Service service = getService(FEATURE_A_SERVICE);
        assertThat(service.getClassLoader().getClass().getName(),
                equalTo("dalvik.system.DelegateLastClassLoader"));
        assertThat(service.getClassLoader().getParent().getClass().getName(),
                equalTo("dalvik.system.PathClassLoader"));
    }

    @Test
    public void testFeatureBServiceClassLoader() throws Exception {
        final Service service = getService(FEATURE_B_SERVICE);
        assertThat(service.getClassLoader().getClass().getName(),
                equalTo("dalvik.system.PathClassLoader"));
        assertThat(service.getClassLoader().getParent().getClass().getName(),
                equalTo("dalvik.system.DelegateLastClassLoader"));
    }

    private Service getService(ComponentName componentName) throws TimeoutException {
        final Intent intent = new Intent();
        intent.setComponent(componentName);
        final BaseService.LocalBinder localBinder = (BaseService.LocalBinder) mServiceTestRule
                .bindService(intent);
        return localBinder.getService();
    }

    private static class ExtrasResultReceiver extends BroadcastReceiver {
        private final CompletableFuture<Bundle> mResult = new CompletableFuture<>();

        @Override
        public void onReceive(Context context, Intent intent) {
            mResult.complete(getResultExtras(true));
        }

        public Bundle get() throws Exception {
            return mResult.get(5000, TimeUnit.SECONDS);
        }
    }

    private static ExtrasResultReceiver sendOrderedBroadcast(Context context) {
        final ExtrasResultReceiver resultReceiver = new ExtrasResultReceiver();
        context.sendOrderedBroadcast(new Intent(PACKAGE + ".ACTION").setPackage(PACKAGE), null,
                resultReceiver, null, 0, null, null);
        return resultReceiver;
    }

    private static class AppContextTestRule implements TestRule {
        private Context mContext;

        @Override
        public Statement apply(final Statement base, Description description) {
            return new Statement() {
                @Override
                public void evaluate() throws Throwable {
                    mContext = InstrumentationRegistry.getInstrumentation().getTargetContext();
                    base.evaluate();
                }
            };
        }

        public Context getContext() {
            return mContext;
        }
    }
}

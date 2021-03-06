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

package android.cts.backup;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.junit.Assume.assumeTrue;

import android.platform.test.annotations.AppModeFull;

import com.android.compatibility.common.util.BackupUtils;
import com.android.compatibility.common.util.LogcatInspector;
import com.android.tradefed.device.DeviceNotAvailableException;
import com.android.tradefed.device.ITestDevice;
import com.android.tradefed.log.LogUtil.CLog;
import com.android.tradefed.testtype.DeviceJUnit4ClassRunner;
import com.android.tradefed.testtype.ITestInformationReceiver;
import com.android.tradefed.testtype.junit4.BaseHostJUnit4Test;

import org.junit.After;
import org.junit.AssumptionViolatedException;
import org.junit.Before;
import org.junit.Rule;
import org.junit.rules.TestRule;
import org.junit.runner.Description;
import org.junit.runner.RunWith;
import org.junit.runners.model.Statement;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Base class for CTS backup/restore hostside tests
 */
@RunWith(DeviceJUnit4ClassRunner.class)
@AppModeFull
public abstract class BaseBackupHostSideTest extends BaseHostJUnit4Test {
    /** Value of PackageManager.FEATURE_BACKUP */
    private static final String FEATURE_BACKUP = "android.software.backup";

    protected static final String LOCAL_TRANSPORT =
            "com.android.localtransport/.LocalTransport";

    @Rule
    public final RequiredFeatureRule mBackupRequiredRule = new RequiredFeatureRule(this,
            FEATURE_BACKUP);

    private BackupUtils mBackupUtils = new BackupUtils() {
        @Override
        protected InputStream executeShellCommand(String command) throws IOException {
            return executeDeviceShellCommand(getDevice(), command);
        }
    };

    protected final LogcatInspector mLogcatInspector = new LogcatInspector() {
        @Override
        protected InputStream executeShellCommand(String command) throws IOException {
            return executeDeviceShellCommand(getDevice(), command);
        }
    };

    @Before
    public void setUp() throws Exception {
        // Check that the backup wasn't disabled and the transport wasn't switched unexpectedly.
        assertTrue("Backup was unexpectedly disabled during the module test run",
                getBackupUtils().isBackupEnabled());
        assertEquals("LocalTransport should be selected at this point", LOCAL_TRANSPORT,
                getCurrentTransport());
        mBackupUtils.wakeAndUnlockDevice();
    }

    protected BackupUtils getBackupUtils() {
        return mBackupUtils;
    }

    /**
     * Attempts to clear the device log.
     */
    protected void clearLogcat() throws DeviceNotAvailableException {
        getDevice().executeAdbCommand("logcat", "-c");
    }

    /**
     * Run test <testName> in test <className> found in package <packageName> on the device, and
     * assert it is successful.
     */
    protected void checkDeviceTest(String packageName, String className, String testName)
            throws DeviceNotAvailableException {
        boolean result = runDeviceTests(packageName, className, testName);
        assertTrue("Device test failed: " + testName, result);
    }

    protected void startActivityInPackageAndWait(String packageName, String className)
            throws DeviceNotAvailableException {
        getDevice().executeShellCommand(String.format(
                "am start -W -a android.intent.action.MAIN -n %s/%s.%s", packageName,
                packageName,
                className));
    }

    /**
     * Clears backup data stored in Local Transport for a package.
     * NB: 'bmgr wipe' does not produce any useful output if the package or transport not found,
     * so we cannot really check the success of the operation
     */
    protected void clearBackupDataInLocalTransport(String packageName)
            throws DeviceNotAvailableException {
        getDevice().executeShellCommand(
                String.format("bmgr wipe %s %s", LOCAL_TRANSPORT, packageName));
    }

    /**
     * Clears package data
     */
    protected void clearPackageData(String packageName) throws DeviceNotAvailableException {
        getDevice().executeShellCommand(String.format("pm clear %s", packageName));
    }

    protected String getCurrentTransport() throws DeviceNotAvailableException {
        String output = getDevice().executeShellCommand("bmgr list transports");
        Pattern pattern = Pattern.compile("\\* (.*)");
        Matcher matcher = pattern.matcher(output);
        if (matcher.find()) {
            return matcher.group(1);
        } else {
            throw new RuntimeException("non-parsable output setting bmgr transport: " + output);
        }
    }

    protected void setLocalTransportParameters(String parameters) throws Exception {
        getDevice().executeShellCommand("settings put secure backup_local_transport_parameters "
                + parameters);
    }

    protected String getLocalTransportParameters() throws DeviceNotAvailableException {
        return getDevice().executeShellCommand(
                "settings get secure backup_local_transport_parameters");
    }

    protected void enableFakeEncryptionOnTransport() throws Exception {
        setLocalTransportParameters("fake_encryption_flag=true");
    }

    protected void disableFakeEncryptionOnTransport() throws Exception {
        setLocalTransportParameters("fake_encryption_flag=false");
    }

    static InputStream executeDeviceShellCommand(
            ITestDevice device, String command) throws IOException {
        try {
            String result = device.executeShellCommand(command);
            return new ByteArrayInputStream(result.getBytes(StandardCharsets.UTF_8));
        } catch (DeviceNotAvailableException e) {
            throw new IOException(e);
        }
    }

    // TODO(b/169341308): move to common infra code
    private static final class RequiredFeatureRule implements TestRule {

        private final ITestInformationReceiver mReceiver;
        private final String mFeature;

        RequiredFeatureRule(ITestInformationReceiver receiver, String feature) {
            mReceiver = receiver;
            mFeature = feature;
        }

        @Override
        public Statement apply(Statement base, Description description) {
            return new Statement() {

                @Override
                public void evaluate() throws Throwable {
                    boolean hasFeature = false;
                    try {
                        hasFeature = mReceiver.getTestInformation().getDevice()
                                .hasFeature(mFeature);
                    } catch (DeviceNotAvailableException e) {
                        CLog.e("Could not check if device has feature %s: %e", mFeature, e);
                        return;
                    }

                    if (!hasFeature) {
                        CLog.d("skipping %s#%s"
                                + " because device does not have feature '%s'",
                                description.getClassName(), description.getMethodName(), mFeature);
                        throw new AssumptionViolatedException("Device does not have feature '"
                                + mFeature + "'");
                    }
                    base.evaluate();
                }
            };
        }

        @Override
        public String toString() {
            return "RequiredFeatureRule[" + mFeature + "]";
        }
    }
}

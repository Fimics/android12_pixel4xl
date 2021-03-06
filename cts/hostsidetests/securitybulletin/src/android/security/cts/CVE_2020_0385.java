/**
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

package android.security.cts;

import android.platform.test.annotations.AsbSecurityTest;
import org.junit.Test;
import org.junit.runner.RunWith;
import com.android.tradefed.testtype.DeviceJUnit4ClassRunner;
import com.android.tradefed.device.ITestDevice;

import static org.junit.Assume.*;

@RunWith(DeviceJUnit4ClassRunner.class)
public class CVE_2020_0385 extends SecurityTestCase {

    /**
     * b/150160041
     * Vulnerability Behaviour: SIGSEGV in self
     */
    @Test
    @AsbSecurityTest(cveBugId = 150160041)
    public void testPocCVE_2020_0385() throws Exception {
        assumeFalse(moduleIsPlayManaged("com.google.android.media"));
        String inputFiles[] = {"cve_2020_0385.xmf", "cve_2020_0385.info"};
        AdbUtils.runPocAssertNoCrashesNotVulnerable("CVE-2020-0385",
                AdbUtils.TMP_PATH + inputFiles[0] + " " + AdbUtils.TMP_PATH + inputFiles[1],
                inputFiles, AdbUtils.TMP_PATH, getDevice());
    }
}

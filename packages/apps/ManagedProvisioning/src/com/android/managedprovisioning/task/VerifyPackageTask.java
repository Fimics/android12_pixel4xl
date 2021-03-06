/*
 * Copyright 2016, The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.android.managedprovisioning.task;

import static com.android.internal.util.Preconditions.checkNotNull;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.text.TextUtils;

import com.android.internal.annotations.VisibleForTesting;
import com.android.managedprovisioning.analytics.MetricsWriterFactory;
import com.android.managedprovisioning.analytics.ProvisioningAnalyticsTracker;
import com.android.managedprovisioning.common.ManagedProvisioningSharedPreferences;
import com.android.managedprovisioning.common.ProvisionLogger;
import com.android.managedprovisioning.common.SettingsFacade;
import com.android.managedprovisioning.common.StoreUtils;
import com.android.managedprovisioning.common.Utils;
import com.android.managedprovisioning.model.PackageDownloadInfo;
import com.android.managedprovisioning.model.ProvisioningParams;

import java.io.File;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

/**
 * Verifies the management app apk downloaded previously in {@link DownloadPackageTask}.
 *
 * <p>The first check verifies that a {@link android.app.admin.DeviceAdminReceiver} is present in
 * the apk and that it corresponds to the one provided via
 * {@link ProvisioningParams#deviceAdminComponentName}.</p>
 *
 * <p>The second check verifies that the package or signature checksum matches the ones given via
 * {@link PackageDownloadInfo#packageChecksum} or {@link PackageDownloadInfo#signatureChecksum}
 * respectively. The package checksum takes priority in case both are present.</p>
 */
public class VerifyPackageTask extends AbstractProvisioningTask {
    public static final int ERROR_HASH_MISMATCH = 0;
    public static final int ERROR_DEVICE_ADMIN_MISSING = 1;

    private final Utils mUtils;
    private final PackageLocationProvider mDownloadLocationProvider;
    private final PackageManager mPackageManager;
    private final PackageDownloadInfo mDownloadInfo;

    public VerifyPackageTask(
            PackageLocationProvider downloadLocationProvider,
            Context context,
            ProvisioningParams params,
            Callback callback) {
        this(new Utils(), downloadLocationProvider, context, params, callback,
                new ProvisioningAnalyticsTracker(
                        MetricsWriterFactory.getMetricsWriter(context, new SettingsFacade()),
                        new ManagedProvisioningSharedPreferences(context)));
    }

    @VisibleForTesting
    VerifyPackageTask(
            Utils utils,
            PackageLocationProvider downloadLocationProvider,
            Context context,
            ProvisioningParams params,
            Callback callback,
            ProvisioningAnalyticsTracker provisioningAnalyticsTracker) {
        super(context, params, callback, provisioningAnalyticsTracker);

        mUtils = checkNotNull(utils);
        mDownloadLocationProvider = checkNotNull(downloadLocationProvider);
        mPackageManager = mContext.getPackageManager();
        mDownloadInfo = checkNotNull(params.deviceAdminDownloadInfo);
    }

    @Override
    public void run(int userId) {
        final File packageLocation = mDownloadLocationProvider.getPackageLocation();
        if (packageLocation == null) {
            ProvisionLogger.logw("VerifyPackageTask invoked, but package is null");
            success();
            return;
        }
        ProvisionLogger.logi("Verifying package from location " + packageLocation.getAbsolutePath()
                + " for user " + userId);

        PackageInfo packageInfo = mPackageManager.getPackageArchiveInfo(
                packageLocation.getAbsolutePath(),
                PackageManager.GET_SIGNATURES | PackageManager.GET_RECEIVERS);
        String packageName = mProvisioningParams.inferDeviceAdminPackageName();
        // Device admin package name can't be null
        if (packageInfo == null || packageName == null) {
            ProvisionLogger.loge("Device admin package info or name is null");
            error(ERROR_DEVICE_ADMIN_MISSING);
            return;
        }

        if (mUtils.findDeviceAdminInPackageInfo(packageName,
                mProvisioningParams.deviceAdminComponentName, packageInfo) == null) {
            error(ERROR_DEVICE_ADMIN_MISSING);
            return;
        }

        if (mDownloadInfo.packageChecksum.length > 0) {
            if (!doesPackageHashMatch(
                    packageLocation.getAbsolutePath(), mDownloadInfo.packageChecksum)) {
                error(ERROR_HASH_MISMATCH);
                return;
            }
        } else {
            if (!doesASignatureHashMatch(packageInfo, mDownloadInfo.signatureChecksum)) {
                error(ERROR_HASH_MISMATCH);
                return;
            }
        }

        success();
    }

    private List<byte[]> computeHashesOfAllSignatures(Signature[] signatures) {
        if (signatures == null) {
            return null;
        }

        List<byte[]> hashes = new LinkedList<>();
        for (Signature signature : signatures) {
            byte[] hash = mUtils.computeHashOfByteArray(signature.toByteArray());
            hashes.add(hash);
        }
        return hashes;
    }

    private boolean doesASignatureHashMatch(PackageInfo packageInfo, byte[] signatureChecksum) {
        // Check whether a signature hash of downloaded apk matches the hash given in constructor.
        ProvisionLogger.logd("Checking " + Utils.SHA256_TYPE
                + "-hashes of all signatures of downloaded package.");
        List<byte[]> sigHashes = computeHashesOfAllSignatures(packageInfo.signatures);
        if (sigHashes == null || sigHashes.isEmpty()) {
            ProvisionLogger.loge("Downloaded package does not have any signatures.");
            return false;
        }

        for (byte[] sigHash : sigHashes) {
            if (Arrays.equals(sigHash, signatureChecksum)) {
                return true;
            }
        }

        ProvisionLogger.loge("Provided hash does not match any signature hash.");
        ProvisionLogger.loge("Hash provided by programmer: "
                + StoreUtils.byteArrayToString(signatureChecksum));
        ProvisionLogger.loge("Hashes computed from package signatures: ");
        for (byte[] sigHash : sigHashes) {
            if (sigHash != null) {
                ProvisionLogger.loge(StoreUtils.byteArrayToString(sigHash));
            }
        }

        return false;
    }

    /**
     * Check whether package hash of downloaded file matches the hash given in PackageDownloadInfo.
     * By default, SHA-256 is used to verify the file hash.
     */
    private boolean doesPackageHashMatch(String downloadLocation, byte[] packageChecksum) {
        byte[] packageSha256Hash = null;

        ProvisionLogger.logd("Checking file hash of entire apk file.");
        packageSha256Hash = mUtils.computeHashOfFile(downloadLocation, Utils.SHA256_TYPE);
        if (Arrays.equals(packageChecksum, packageSha256Hash)) {
            return true;
        }

        ProvisionLogger.loge("Provided hash does not match file hash.");
        ProvisionLogger.loge("Hash provided by programmer: "
                + StoreUtils.byteArrayToString(packageChecksum));
        if (packageSha256Hash != null) {
            ProvisionLogger.loge("SHA-256 Hash computed from file: "
                    + StoreUtils.byteArrayToString(packageSha256Hash));
        }
        return false;
    }
}

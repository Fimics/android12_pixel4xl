/*
 * Copyright (C) 2018 The Android Open Source Project
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

package com.android.car.settings.system;

import android.content.ActivityNotFoundException;
import android.content.ContentResolver;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.SystemProperties;
import android.text.TextUtils;
import android.widget.Toast;

import androidx.core.content.FileProvider;
import androidx.fragment.app.FragmentActivity;
import androidx.loader.app.LoaderManager;
import androidx.loader.content.Loader;

import com.android.car.settings.R;
import com.android.car.settings.common.Logger;
import com.android.settingslib.core.lifecycle.HideNonSystemOverlayMixin;

import java.io.File;

/**
 * The activity that displays third-party licenses.
 */
public class ThirdPartyLicensesActivity extends FragmentActivity implements
        LoaderManager.LoaderCallbacks<File> {
    private static final Logger LOG = new Logger(ThirdPartyLicensesActivity.class);
    private static final int LOADER_ID_LICENSE_HTML_LOADER = 0;
    private static final String DEFAULT_LICENSE_PATH = "/system/etc/NOTICE.html.gz";
    private static final String PROPERTY_LICENSE_PATH = "ro.config.license_path";
    private static final String FILE_PROVIDER_AUTHORITY = "com.android.settings.files";
    private static final String HTML_VIEWER_PACKAGE = "com.android.htmlviewer";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getLifecycle().addObserver(new HideNonSystemOverlayMixin(this));

        final String licenseHtmlPath =
                SystemProperties.get(PROPERTY_LICENSE_PATH, DEFAULT_LICENSE_PATH);
        if (isFilePathValid(licenseHtmlPath)) {
            showSelectedFile(licenseHtmlPath);
        } else {
            showHtmlFromDefaultXmlFiles();
        }
    }

    @Override
    public Loader<File> onCreateLoader(int id, Bundle args) {
        return new LicenseHtmlLoader(this);
    }

    @Override
    public void onLoadFinished(Loader<File> loader, File generatedHtmlFile) {
        showGeneratedHtmlFile(generatedHtmlFile);
    }

    @Override
    public void onLoaderReset(Loader<File> loader) {
    }

    private void showSelectedFile(final String path) {
        if (TextUtils.isEmpty(path)) {
            LOG.e("The system property for the license file is empty");
            showErrorAndFinish();
            return;
        }

        final File file = new File(path);
        if (!isFileValid(file)) {
            LOG.e("License file " + path + " does not exist");
            showErrorAndFinish();
            return;
        }
        showHtmlFromUri(Uri.fromFile(file));
    }

    private void showErrorAndFinish() {
        Toast.makeText(this, R.string.settings_license_activity_unavailable, Toast.LENGTH_LONG)
                .show();
        finish();
    }

    private void showHtmlFromUri(Uri uri) {
        // Kick off external viewer due to WebView security restrictions; we
        // carefully point it at HTMLViewer, since it offers to decompress
        // before viewing.
        final Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setDataAndType(uri, "text/html");
        intent.putExtra(Intent.EXTRA_TITLE, getString(R.string.settings_license_activity_title));
        if (ContentResolver.SCHEME_CONTENT.equals(uri.getScheme())) {
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        }
        intent.addCategory(Intent.CATEGORY_DEFAULT);
        intent.setPackage(HTML_VIEWER_PACKAGE);

        try {
            startActivity(intent);
            finish();
        } catch (ActivityNotFoundException e) {
            LOG.e("Failed to find viewer", e);
            showErrorAndFinish();
        }
    }

    private void showHtmlFromDefaultXmlFiles() {
        LoaderManager.getInstance(this).initLoader(LOADER_ID_LICENSE_HTML_LOADER, Bundle.EMPTY,
                this);
    }

    private void showGeneratedHtmlFile(File generatedHtmlFile) {
        if (generatedHtmlFile != null) {
            LOG.i("File size: " + generatedHtmlFile.length());
            showHtmlFromUri(getUriFromGeneratedHtmlFile(generatedHtmlFile));
        } else {
            LOG.e("Failed to generate.");
            showErrorAndFinish();
        }
    }

    private Uri getUriFromGeneratedHtmlFile(File generatedHtmlFile) {
        return FileProvider.getUriForFile(this, FILE_PROVIDER_AUTHORITY, generatedHtmlFile);
    }

    private boolean isFilePathValid(final String path) {
        return !TextUtils.isEmpty(path) && isFileValid(new File(path));
    }

    private boolean isFileValid(final File file) {
        return file.exists() && file.length() != 0;
    }
}

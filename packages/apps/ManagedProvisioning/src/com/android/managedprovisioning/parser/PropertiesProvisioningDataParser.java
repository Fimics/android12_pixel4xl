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

package com.android.managedprovisioning.parser;

import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_ADMIN_EXTRAS_BUNDLE;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_DEVICE_ADMIN_MINIMUM_VERSION_CODE;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_COOKIE_HEADER;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_DEVICE_ADMIN_PACKAGE_NAME;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_LOCALE;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_LOCAL_TIME;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_SENSORS_PERMISSION_GRANT_OPT_OUT;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_SKIP_ENCRYPTION;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_TIME_ZONE;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_USE_MOBILE_DATA;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_ANONYMOUS_IDENTITY;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_CA_CERTIFICATE;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_DOMAIN;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_EAP_METHOD;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_HIDDEN;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_IDENTITY;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_PAC_URL;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_PASSWORD;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_PHASE2_AUTH;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_PROXY_BYPASS;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_PROXY_HOST;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_PROXY_PORT;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_SECURITY_TYPE;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_SSID;
import static android.app.admin.DevicePolicyManager.EXTRA_PROVISIONING_WIFI_USER_CERTIFICATE;
import static android.app.admin.DevicePolicyManager.MIME_TYPE_PROVISIONING_NFC;
import static android.nfc.NfcAdapter.ACTION_NDEF_DISCOVERED;

import static com.android.internal.util.Preconditions.checkNotNull;

import static java.nio.charset.StandardCharsets.UTF_8;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.nfc.NdefMessage;
import android.nfc.NdefRecord;
import android.nfc.NfcAdapter;
import android.os.Parcelable;
import android.os.PersistableBundle;

import androidx.annotation.Nullable;
import androidx.annotation.VisibleForTesting;

import com.android.managedprovisioning.common.IllegalProvisioningArgumentException;
import com.android.managedprovisioning.common.ManagedProvisioningSharedPreferences;
import com.android.managedprovisioning.common.ProvisionLogger;
import com.android.managedprovisioning.common.SettingsFacade;
import com.android.managedprovisioning.common.StoreUtils;
import com.android.managedprovisioning.model.PackageDownloadInfo;
import com.android.managedprovisioning.model.ProvisioningParams;
import com.android.managedprovisioning.model.WifiInfo;

import java.io.IOException;
import java.io.StringReader;
import java.util.IllformedLocaleException;
import java.util.Properties;


/**
 * A parser which parses provisioning data from intent which stores in {@link Properties}.
 *
 * <p>It is used to parse an intent contains the extra {@link NfcAdapter.EXTRA_NDEF_MESSAGES}, which
 * indicates that provisioning was started via Nfc bump. This extra contains an NDEF message, which
 * contains an NfcRecord with mime type {@link MIME_TYPE_PROVISIONING_NFC}. This record stores a
 * serialized properties object, which contains the serialized extras described in the next option.
 * A typical use case would be a programmer application that sends an Nfc bump to start Nfc
 * provisioning from a programmer device.
 */
@VisibleForTesting
public class PropertiesProvisioningDataParser implements ProvisioningDataParser {

    private final ParserUtils mParserUtils;
    private final Context mContext;
    private final ManagedProvisioningSharedPreferences mSharedPreferences;
    private final SettingsFacade mSettingsFacade;

    PropertiesProvisioningDataParser(Context context, ParserUtils parserUtils,
            SettingsFacade settingsFacade) {
        this(context, parserUtils, settingsFacade,
                new ManagedProvisioningSharedPreferences(context));
    }

    @VisibleForTesting
    PropertiesProvisioningDataParser(Context context, ParserUtils parserUtils,
            SettingsFacade settingsFacade, ManagedProvisioningSharedPreferences sharedPreferences) {
        mContext = checkNotNull(context);
        mParserUtils = checkNotNull(parserUtils);
        mSettingsFacade = checkNotNull(settingsFacade);
        mSharedPreferences = checkNotNull(sharedPreferences);
    }

    @Nullable
    private String getPropertyFromLongName(Properties properties, String longName) {
        if (properties.containsKey(longName)) {
            return properties.getProperty(longName);
        }
        String shortName = ExtrasProvisioningDataParser.getShortExtraNames(longName);
        if (properties.containsKey(shortName)) {
            return properties.getProperty(shortName);
        }
        return null;
    }

    public ProvisioningParams parse(Intent nfcIntent)
            throws IllegalProvisioningArgumentException {
        if (!ACTION_NDEF_DISCOVERED.equals(nfcIntent.getAction())) {
            throw new IllegalProvisioningArgumentException(
                    "Only NFC action is supported in this parser.");
        }

        ProvisionLogger.logi("Processing Nfc Payload.");
        NdefRecord firstRecord = getFirstNdefRecord(nfcIntent);
        if (firstRecord != null) {
            try {
                Properties props = new Properties();
                props.load(new StringReader(new String(firstRecord.getPayload(), UTF_8)));

                // For parsing non-string parameters.
                String s = null;

                ProvisioningParams.Builder builder = ProvisioningParams.Builder.builder()
                        .setProvisioningId(mSharedPreferences.incrementAndGetProvisioningId())
                        .setStartedByTrustedSource(true)
                        .setIsNfc(true)
                        .setProvisioningAction(mParserUtils.extractProvisioningAction(
                                nfcIntent, mSettingsFacade, mContext))
                        .setDeviceAdminPackageName(
                                getPropertyFromLongName(
                                        props, EXTRA_PROVISIONING_DEVICE_ADMIN_PACKAGE_NAME));
                if ((s = getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME))
                        != null) {
                    builder.setDeviceAdminComponentName(ComponentName.unflattenFromString(s));
                }

                // Parse time zone, locale and local time.
                builder.setTimeZone(getPropertyFromLongName(props, EXTRA_PROVISIONING_TIME_ZONE))
                        .setLocale(StoreUtils.stringToLocale(
                                getPropertyFromLongName(props, EXTRA_PROVISIONING_LOCALE)));
                if ((s = getPropertyFromLongName(props, EXTRA_PROVISIONING_LOCAL_TIME)) != null) {
                    builder.setLocalTime(Long.parseLong(s));
                }

                // Parse WiFi configuration.
                builder.setWifiInfo(parseWifiInfoFromProperties(props))
                        // Parse device admin package download info.
                        .setDeviceAdminDownloadInfo(parsePackageDownloadInfoFromProperties(props))
                        // Parse EMM customized key-value pairs.
                        // Note: EXTRA_PROVISIONING_ADMIN_EXTRAS_BUNDLE property contains a
                        // Properties object serialized into String. See Properties.store() and
                        // Properties.load() for more details. The property value is optional.
                        .setAdminExtrasBundle(deserializeExtrasBundle(props,
                                EXTRA_PROVISIONING_ADMIN_EXTRAS_BUNDLE));
                if ((s = getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED)) != null) {
                    builder.setLeaveAllSystemAppsEnabled(Boolean.parseBoolean(s));
                }
                if ((s = getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_SKIP_ENCRYPTION)) != null) {
                    builder.setSkipEncryption(Boolean.parseBoolean(s));
                }
                if ((s = getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_USE_MOBILE_DATA)) != null) {
                    builder.setUseMobileData(Boolean.parseBoolean(s));
                }
                if ((s = getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_SENSORS_PERMISSION_GRANT_OPT_OUT)) != null) {
                    builder.setDeviceOwnerPermissionGrantOptOut(Boolean.parseBoolean(s));
                }
                builder.setIsOrganizationOwnedProvisioning(true);
                // TODO(b/177849035): Remove NFC-specific logic
                builder.setReturnBeforePolicyCompliance(true);
                ProvisionLogger.logi("End processing Nfc Payload.");
                return builder.build();
            } catch (IOException e) {
                throw new IllegalProvisioningArgumentException("Couldn't load payload", e);
            } catch (NumberFormatException e) {
                throw new IllegalProvisioningArgumentException("Incorrect numberformat.", e);
            } catch (IllformedLocaleException e) {
                throw new IllegalProvisioningArgumentException("Invalid locale.", e);
            } catch (IllegalArgumentException e) {
                throw new IllegalProvisioningArgumentException("Invalid parameter found!", e);
            } catch (NullPointerException e) {
                throw new IllegalProvisioningArgumentException(
                        "Compulsory parameter not found!", e);
            }
        }
        throw new IllegalProvisioningArgumentException(
                "Intent does not contain NfcRecord with the correct MIME type.");
    }

    /**
     * Parses Wifi configuration from an {@link Properties} and returns the result in
     * {@link WifiInfo}.
     */
    @Nullable
    private WifiInfo parseWifiInfoFromProperties(Properties props) {
        if (getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_SSID) == null) {
            return null;
        }
        WifiInfo.Builder builder = WifiInfo.Builder.builder()
                .setSsid(getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_SSID))
                .setSecurityType(getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_WIFI_SECURITY_TYPE))
                .setPassword(getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_PASSWORD))
                .setEapMethod(getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_EAP_METHOD))
                .setPhase2Auth(getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_PHASE2_AUTH))
                .setCaCertificate(getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_WIFI_CA_CERTIFICATE))
                .setUserCertificate(getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_WIFI_USER_CERTIFICATE))
                .setIdentity(getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_IDENTITY))
                .setAnonymousIdentity(getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_WIFI_ANONYMOUS_IDENTITY))
                .setDomain(getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_DOMAIN))
                .setProxyHost(getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_PROXY_HOST))
                .setProxyBypassHosts(getPropertyFromLongName(
                        props, EXTRA_PROVISIONING_WIFI_PROXY_BYPASS))
                .setPacUrl(getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_PAC_URL));
        // For parsing non-string parameters.
        String s = null;
        if ((s = getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_PROXY_PORT)) != null) {
            builder.setProxyPort(Integer.parseInt(s));
        }
        if ((s = getPropertyFromLongName(props, EXTRA_PROVISIONING_WIFI_HIDDEN)) != null) {
            builder.setHidden(Boolean.parseBoolean(s));
        }

        return builder.build();
    }

    /**
     * Parses device admin package download info from an {@link Properties} and returns the result
     * in {@link PackageDownloadInfo}.
     */
    @Nullable
    private PackageDownloadInfo parsePackageDownloadInfoFromProperties(Properties props) {
        if (getPropertyFromLongName(
                props, EXTRA_PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION) == null) {
            return null;
        }
        PackageDownloadInfo.Builder builder = PackageDownloadInfo.Builder.builder()
                .setLocation(getPropertyFromLongName(props,
                        EXTRA_PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION))
                .setCookieHeader(getPropertyFromLongName(props,
                        EXTRA_PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_COOKIE_HEADER));
        // For parsing non-string parameters.
        String s = null;
        if ((s = getPropertyFromLongName(
                props, EXTRA_PROVISIONING_DEVICE_ADMIN_MINIMUM_VERSION_CODE)) != null) {
            builder.setMinVersion(Integer.parseInt(s));
        }
        if ((s = getPropertyFromLongName(
                props, EXTRA_PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM)) != null) {
            builder.setPackageChecksum(StoreUtils.stringToByteArray(s));
        }
        if ((s = getPropertyFromLongName(props, EXTRA_PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM))
                != null) {
            builder.setSignatureChecksum(StoreUtils.stringToByteArray(s));
        }
        return builder.build();
    }

    /**
     * Get a {@link PersistableBundle} from a String property in a Properties object.
     * @param props the source of the extra
     * @param extraName key into the Properties object
     * @return the bundle or {@code null} if there was no property with the given name
     * @throws IOException if there was an error parsing the propery
     */
    private PersistableBundle deserializeExtrasBundle(Properties props, String extraName)
            throws IOException {
        PersistableBundle extrasBundle = null;
        String serializedExtras = getPropertyFromLongName(props, extraName);
        if (serializedExtras != null) {
            Properties extrasProp = new Properties();
            extrasProp.load(new StringReader(serializedExtras));
            extrasBundle = new PersistableBundle(extrasProp.size());
            for (String propName : extrasProp.stringPropertyNames()) {
                extrasBundle.putString(propName, extrasProp.getProperty(propName));
            }
        }
        return extrasBundle;
    }

    /**
     * @return the first {@link NdefRecord} found with a recognized MIME-type
     */
    public static NdefRecord getFirstNdefRecord(Intent nfcIntent) {
        // Only one first message with NFC_MIME_TYPE is used.
        final Parcelable[] ndefMessages = nfcIntent.getParcelableArrayExtra(
                NfcAdapter.EXTRA_NDEF_MESSAGES);
        if (ndefMessages != null) {
            for (Parcelable rawMsg : ndefMessages) {
                NdefMessage msg = (NdefMessage) rawMsg;
                for (NdefRecord record : msg.getRecords()) {
                    String mimeType = new String(record.getType(), UTF_8);

                    if (MIME_TYPE_PROVISIONING_NFC.equals(mimeType)) {
                        return record;
                    }

                    // Assume only first record of message is used.
                    break;
                }
            }
        }
        return null;
    }
}

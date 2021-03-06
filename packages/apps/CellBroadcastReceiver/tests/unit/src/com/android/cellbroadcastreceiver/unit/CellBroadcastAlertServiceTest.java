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
 * limitations under the License
 */

package com.android.cellbroadcastreceiver.unit;

import static com.android.cellbroadcastreceiver.CellBroadcastAlertAudio.ALERT_AUDIO_TONE_TYPE;
import static com.android.cellbroadcastreceiver.CellBroadcastAlertService.SHOW_NEW_ALERT_ACTION;

import static org.junit.Assert.assertArrayEquals;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doReturn;

import android.content.Intent;
import android.provider.Telephony;
import android.telephony.AccessNetworkConstants;
import android.telephony.NetworkRegistrationInfo;
import android.telephony.ServiceState;
import android.telephony.SmsCbCmasInfo;
import android.telephony.SmsCbEtwsInfo;
import android.telephony.SmsCbLocation;
import android.telephony.SmsCbMessage;

import com.android.cellbroadcastreceiver.CellBroadcastAlertAudio;
import com.android.cellbroadcastreceiver.CellBroadcastAlertService;
import com.android.cellbroadcastreceiver.CellBroadcastSettings;
import com.android.internal.telephony.gsm.SmsCbConstants;

import org.junit.After;
import org.junit.Before;
import org.mockito.Mock;

import java.util.ArrayList;

public class CellBroadcastAlertServiceTest extends
        CellBroadcastServiceTestCase<CellBroadcastAlertService> {
    @Mock
    ServiceState mockSS;

    public CellBroadcastAlertServiceTest() {
        super(CellBroadcastAlertService.class);
    }

    static SmsCbMessage createMessage(int serialNumber) {
        return createMessageForCmasMessageClass(serialNumber,
                SmsCbConstants.MESSAGE_ID_CMAS_ALERT_PRESIDENTIAL_LEVEL, 0);
    }

    static SmsCbMessage createMessageForCmasMessageClass(int serialNumber,
            int serviceCategory, int cmasMessageClass) {
        return new SmsCbMessage(1, 2, serialNumber, new SmsCbLocation(), serviceCategory,
                "language", "body",
                SmsCbMessage.MESSAGE_PRIORITY_EMERGENCY, null,
                new SmsCbCmasInfo(cmasMessageClass, 2, 3, 4, 5, 6),
                0, 1);
    }

    static SmsCbMessage createCmasMessageWithLanguage(int serialNumber, int serviceCategory,
            int cmasMessageClass, String language) {
        return new SmsCbMessage(1, 2, serialNumber, new SmsCbLocation(),
                serviceCategory, language, "body",
                SmsCbMessage.MESSAGE_PRIORITY_EMERGENCY, null,
                new SmsCbCmasInfo(cmasMessageClass, 2, 3, 4, 5, 6),
                0, 1);
    }

    @Before
    public void setUp() throws Exception {
        super.setUp();
    }

    @After
    public void tearDown() throws Exception {
        super.tearDown();
    }

    private static void compareEtwsWarningInfo(SmsCbEtwsInfo info1, SmsCbEtwsInfo info2) {
        if (info1 == info2) return;
        assertEquals(info1.toString(), info2.toString());
        assertArrayEquals(info1.getPrimaryNotificationSignature(),
                info2.getPrimaryNotificationSignature());
        assertEquals(info1.isPrimary(), info2.isPrimary());
    }

    private static void compareCmasWarningInfo(SmsCbCmasInfo info1, SmsCbCmasInfo info2) {
        if (info1 == info2) return;
        assertEquals(info1.getCategory(), info2.getCategory());
        assertEquals(info1.getCertainty(), info2.getCertainty());
        assertEquals(info1.getMessageClass(), info2.getMessageClass());
        assertEquals(info1.getResponseType(), info2.getResponseType());
        assertEquals(info1.getSeverity(), info2.getSeverity());
        assertEquals(info1.getUrgency(), info2.getUrgency());
    }

    private static void compareCellBroadCastMessage(SmsCbMessage m1, SmsCbMessage m2) {
        if (m1 == m2) return;
        assertEquals(m1.getCmasWarningInfo().getMessageClass(),
                m2.getCmasWarningInfo().getMessageClass());
        compareCmasWarningInfo(m1.getCmasWarningInfo(), m2.getCmasWarningInfo());
        compareEtwsWarningInfo(m1.getEtwsWarningInfo(), m2.getEtwsWarningInfo());
        assertEquals(m1.getLanguageCode(), m2.getLanguageCode());
        assertEquals(m1.getMessageBody(), m2.getMessageBody());
        assertEquals(m1.getServiceCategory(), m2.getServiceCategory());
        assertEquals(m1.getSerialNumber(), m2.getSerialNumber());
    }

    private void sendMessage(int serialNumber) {
        Intent intent = new Intent(mContext, CellBroadcastAlertService.class);
        intent.setAction(Telephony.Sms.Intents.ACTION_SMS_EMERGENCY_CB_RECEIVED);

        SmsCbMessage m = createMessage(serialNumber);
        sendMessage(m, intent);
    }

    private void sendMessageForCmasMessageClass(int serialNumber, int cmasMessageClass) {
        Intent intent = new Intent(mContext, CellBroadcastAlertService.class);
        intent.setAction(Telephony.Sms.Intents.ACTION_SMS_EMERGENCY_CB_RECEIVED);

        SmsCbMessage m = createMessageForCmasMessageClass(serialNumber, cmasMessageClass,
                cmasMessageClass);
        sendMessage(m, intent);
    }

    private void sendMessageForCmasMessageClassAndLanguage(int serialNumber, int cmasMessageClass,
            String language) {
        Intent intent = new Intent(mContext, CellBroadcastAlertService.class);
        intent.setAction(Telephony.Sms.Intents.ACTION_SMS_EMERGENCY_CB_RECEIVED);

        SmsCbMessage m = createCmasMessageWithLanguage(serialNumber, cmasMessageClass,
                cmasMessageClass, language);
        sendMessage(m, intent);
    }

    private void sendMessage(SmsCbMessage m, Intent intent) {
        intent.putExtra("message", m);
        startService(intent);
    }

    private void waitForServiceIntent() {
        waitFor(() -> mServiceIntentToVerify != null);
    }

    // Test handleCellBroadcastIntent method
    @InstrumentationTest
    // This test has a module dependency, so it is disabled for OEM testing because it is not a true
    // unit test
    public void testHandleCellBroadcastIntent() {
        doReturn(new String[]{"0x1112:rat=gsm, emergency=true"})
                .when(mResources).getStringArray(
                        eq(com.android.cellbroadcastreceiver.R.array.etws_alerts_range_strings));
        enablePreference(CellBroadcastSettings.KEY_ENABLE_ALERTS_MASTER_TOGGLE);
        sendMessage(987654321);
        waitForServiceIntent();

        assertEquals(SHOW_NEW_ALERT_ACTION, mServiceIntentToVerify.getAction());

        SmsCbMessage cbmTest = (SmsCbMessage) mServiceIntentToVerify.getExtras().get("message");
        SmsCbMessage cbm = createMessage(987654321);

        compareCellBroadCastMessage(cbm, cbmTest);
    }

    // Test testHandleCellBroadcastIntentDomesticRoaming method
    @InstrumentationTest
    // This test has a module dependency, so it is disabled for OEM testing because it is not a true
    // unit test
    public void testHandleCellBroadcastIntentDomesticRoaming() throws Exception {
        doReturn(mockSS).when(mMockedTelephonyManager).getServiceState();
        NetworkRegistrationInfo mockNeRegInfo = new NetworkRegistrationInfo(
                NetworkRegistrationInfo.DOMAIN_CS, AccessNetworkConstants.TRANSPORT_TYPE_WWAN,
                NetworkRegistrationInfo.REGISTRATION_STATE_ROAMING, 0, 0, false,
                null, null, "", true, 0, 0, 0);
        mockNeRegInfo.setRoamingType(ServiceState.ROAMING_TYPE_DOMESTIC);
        doReturn(mockNeRegInfo).when(mockSS).getNetworkRegistrationInfo(anyInt(), anyInt());
        doReturn(new String[]{"0x1112:rat=gsm, emergency=true, scope=domestic"})
                .when(mResources).getStringArray(
                        eq(com.android.cellbroadcastreceiver.R.array.etws_alerts_range_strings));

        enablePreference(CellBroadcastSettings.KEY_ENABLE_ALERTS_MASTER_TOGGLE);
        sendMessage(987654321);
        waitForServiceIntent();

        assertEquals(SHOW_NEW_ALERT_ACTION, mServiceIntentToVerify.getAction());

        SmsCbMessage cbmTest = (SmsCbMessage) mServiceIntentToVerify.getExtras().get("message");
        SmsCbMessage cbm = createMessage(987654321);

        compareCellBroadCastMessage(cbm, cbmTest);
    }

    // Test testHandleCellBroadcastIntentInternationalRoaming method
    @InstrumentationTest
    // This test has a module dependency, so it is disabled for OEM testing because it is not a true
    // unit test
    public void testHandleCellBroadcastIntentInternationalRoaming() throws Exception {
        doReturn(mockSS).when(mMockedTelephonyManager).getServiceState();
        NetworkRegistrationInfo mockNeRegInfo = new NetworkRegistrationInfo(
                NetworkRegistrationInfo.DOMAIN_CS, AccessNetworkConstants.TRANSPORT_TYPE_WWAN,
                NetworkRegistrationInfo.REGISTRATION_STATE_ROAMING, 0, 0, false,
                null, null, "", true, 0, 0, 0);
        mockNeRegInfo.setRoamingType(ServiceState.ROAMING_TYPE_INTERNATIONAL);
        doReturn(mockNeRegInfo).when(mockSS).getNetworkRegistrationInfo(anyInt(), anyInt());
        doReturn(new String[]{"0x1112:rat=gsm, emergency=true, scope=international"})
                .when(mResources).getStringArray(
                        eq(com.android.cellbroadcastreceiver.R.array.etws_alerts_range_strings));

        enablePreference(CellBroadcastSettings.KEY_ENABLE_ALERTS_MASTER_TOGGLE);
        sendMessage(987654321);
        waitForServiceIntent();

        assertEquals(SHOW_NEW_ALERT_ACTION, mServiceIntentToVerify.getAction());

        SmsCbMessage cbmTest = (SmsCbMessage) mServiceIntentToVerify.getExtras().get("message");
        SmsCbMessage cbm = createMessage(987654321);

        compareCellBroadCastMessage(cbm, cbmTest);
    }

    // Test testHandleCellBroadcastIntentNonRoaming method
    @InstrumentationTest
    // This test has a module dependency, so it is disabled for OEM testing because it is not a true
    // unit test
    public void testHandleCellBroadcastIntentNonRoaming() throws Exception {
        doReturn(mockSS).when(mMockedTelephonyManager).getServiceState();
        NetworkRegistrationInfo mockNeRegInfo = new NetworkRegistrationInfo(
                NetworkRegistrationInfo.DOMAIN_CS, AccessNetworkConstants.TRANSPORT_TYPE_WWAN,
                NetworkRegistrationInfo.REGISTRATION_STATE_HOME, 0, 0, false,
                null, null, "", true, 0, 0, 0);
        mockNeRegInfo.setRoamingType(ServiceState.ROAMING_TYPE_NOT_ROAMING);
        doReturn(mockNeRegInfo).when(mockSS).getNetworkRegistrationInfo(anyInt(), anyInt());
        doReturn(new String[]{"0x1112:rat=gsm, emergency=true, scope=international"})
                .when(mResources).getStringArray(
                        eq(com.android.cellbroadcastreceiver.R.array.etws_alerts_range_strings));

        enablePreference(CellBroadcastSettings.KEY_ENABLE_ALERTS_MASTER_TOGGLE);
        sendMessage(987654321);
        waitForServiceIntent();
        assertEquals(SHOW_NEW_ALERT_ACTION, mServiceIntentToVerify.getAction());

        SmsCbMessage cbmTest = (SmsCbMessage) mServiceIntentToVerify.getExtras().get("message");
        SmsCbMessage cbm = createMessage(987654321);

        compareCellBroadCastMessage(cbm, cbmTest);
    }

    // Test testHandleCellBroadcastIntentNonMatchedScope method
    @InstrumentationTest
    // This test has a module dependency, so it is disabled for OEM testing because it is not a true
    // unit test
    public void testHandleCellBroadcastIntentNonMatchedScope() throws Exception {
        doReturn(mockSS).when(mMockedTelephonyManager).getServiceState();
        NetworkRegistrationInfo mockNeRegInfo = new NetworkRegistrationInfo(
                NetworkRegistrationInfo.DOMAIN_CS, AccessNetworkConstants.TRANSPORT_TYPE_WWAN,
                NetworkRegistrationInfo.REGISTRATION_STATE_HOME, 0, 0, false,
                null, null, "", true, 0, 0, 0);
        mockNeRegInfo.setRoamingType(ServiceState.ROAMING_TYPE_DOMESTIC);
        doReturn(mockNeRegInfo).when(mockSS).getNetworkRegistrationInfo(anyInt(), anyInt());
        doReturn(new String[]{"0x1112:rat=gsm, emergency=true, scope=international"})
                .when(mResources).getStringArray(
                        eq(com.android.cellbroadcastreceiver.R.array.etws_alerts_range_strings));

        enablePreference(CellBroadcastSettings.KEY_ENABLE_ALERTS_MASTER_TOGGLE);
        sendMessage(987654321);
        waitForServiceIntent();
        assertNull(mServiceIntentToVerify);
    }

    // Test showNewAlert method
    @InstrumentationTest
    // This test has a module dependency, so it is disabled for OEM testing because it is not a true
    // unit test
    public void testShowNewAlert() {
        Intent intent = new Intent(mContext, CellBroadcastAlertService.class);
        intent.setAction(SHOW_NEW_ALERT_ACTION);
        SmsCbMessage message = createMessage(34788612);
        intent.putExtra("message", message);
        startService(intent);
        waitForServiceIntent();

        // verify audio service intent
        assertEquals(CellBroadcastAlertAudio.ACTION_START_ALERT_AUDIO,
                mServiceIntentToVerify.getAction());
        assertEquals(CellBroadcastAlertService.AlertType.DEFAULT,
                mServiceIntentToVerify.getSerializableExtra(ALERT_AUDIO_TONE_TYPE));
        assertEquals(message.getMessageBody(),
                mServiceIntentToVerify.getStringExtra(
                        CellBroadcastAlertAudio.ALERT_AUDIO_MESSAGE_BODY));

        // verify alert dialog activity intent
        ArrayList<SmsCbMessage> newMessageList = mActivityIntentToVerify
                .getParcelableArrayListExtra(CellBroadcastAlertService.SMS_CB_MESSAGE_EXTRA);
        assertEquals(1, newMessageList.size());
        assertEquals(Intent.FLAG_ACTIVITY_NEW_TASK,
                (mActivityIntentToVerify.getFlags() & Intent.FLAG_ACTIVITY_NEW_TASK));
        compareCellBroadCastMessage(message, newMessageList.get(0));
    }

    // Test showNewAlert method with a CMAS child abduction alert, using the default language code
    @InstrumentationTest
    // This test has a module dependency, so it is disabled for OEM testing because it is not a true
    // unit test
    public void testShowNewAlertChildAbductionWithDefaultLanguage() {
        enablePreference(CellBroadcastSettings.KEY_ENABLE_ALERTS_MASTER_TOGGLE);
        doReturn(new String[]{"0x111B:rat=gsm, emergency=true"})
                .when(mResources).getStringArray(
                        eq(com.android.cellbroadcastreceiver.R.array.etws_alerts_range_strings));
        doReturn("").when(mResources).getString(anyInt());

        sendMessageForCmasMessageClass(34788613,
                SmsCbConstants.MESSAGE_ID_CMAS_ALERT_CHILD_ABDUCTION_EMERGENCY);
        waitForServiceIntent();

        assertEquals(SHOW_NEW_ALERT_ACTION, mServiceIntentToVerify.getAction());

        SmsCbMessage cbmTest = (SmsCbMessage) mServiceIntentToVerify.getExtras().get("message");
        SmsCbMessage cbm = createMessageForCmasMessageClass(34788613,
                SmsCbConstants.MESSAGE_ID_CMAS_ALERT_CHILD_ABDUCTION_EMERGENCY,
                SmsCbConstants.MESSAGE_ID_CMAS_ALERT_CHILD_ABDUCTION_EMERGENCY);

        compareCellBroadCastMessage(cbm, cbmTest);
    }

    // Test showNewAlert method with a CMAS child abduction alert
    @InstrumentationTest
    // This test has a module dependency, so it is disabled for OEM testing because it is not a true
    // unit test
    public void testShowNewAlertChildAbduction() {
        enablePreference(CellBroadcastSettings.KEY_ENABLE_ALERTS_MASTER_TOGGLE);
        enablePreference(CellBroadcastSettings.KEY_RECEIVE_CMAS_IN_SECOND_LANGUAGE);

        final String language = "es";
        doReturn(new String[]{"0x111B:rat=gsm, emergency=true, filter_language=true"})
                .when(mResources).getStringArray(
                        eq(com.android.cellbroadcastreceiver.R.array.etws_alerts_range_strings));
        doReturn(language).when(mResources).getString(anyInt());

        sendMessageForCmasMessageClassAndLanguage(34788614,
                SmsCbConstants.MESSAGE_ID_CMAS_ALERT_CHILD_ABDUCTION_EMERGENCY, language);
        waitForServiceIntent();

        assertEquals(SHOW_NEW_ALERT_ACTION, mServiceIntentToVerify.getAction());

        SmsCbMessage cbmTest = (SmsCbMessage) mServiceIntentToVerify.getExtras().get("message");
        SmsCbMessage cbm = createCmasMessageWithLanguage(34788614,
                SmsCbConstants.MESSAGE_ID_CMAS_ALERT_CHILD_ABDUCTION_EMERGENCY,
                SmsCbConstants.MESSAGE_ID_CMAS_ALERT_CHILD_ABDUCTION_EMERGENCY, language);

        compareCellBroadCastMessage(cbm, cbmTest);
    }

    public void testShouldDisplayMessage() {
        sendMessage(1);
        waitForServiceIntent();

        CellBroadcastAlertService cellBroadcastAlertService =
                (CellBroadcastAlertService) getService();

        // shouldDisplayMessage should return true for ETWS message
        SmsCbEtwsInfo etwsInfo = new SmsCbEtwsInfo(SmsCbEtwsInfo.ETWS_WARNING_TYPE_EARTHQUAKE, true,
                true, true, null);
        SmsCbMessage message = new SmsCbMessage(1, 2, 3, new SmsCbLocation(),
                SmsCbEtwsInfo.ETWS_WARNING_TYPE_EARTHQUAKE,
                "language", "body",
                SmsCbMessage.MESSAGE_PRIORITY_EMERGENCY, etwsInfo,
                null, 0, 1);

        enablePreference(CellBroadcastSettings.KEY_ENABLE_ALERTS_MASTER_TOGGLE);

        assertNotNull("Message should have non-null ETWS info", message.getEtwsWarningInfo());
        assertTrue("Message should be ETWS message", message.isEtwsMessage());
        assertTrue("Should display ETWS message",
                cellBroadcastAlertService.shouldDisplayMessage(message));
    }
}

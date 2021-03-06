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

package com.googlecode.android_scripting.facade.bluetooth;

import android.app.Service;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothHeadsetClient;
import android.bluetooth.BluetoothProfile;
import android.bluetooth.BluetoothUuid;
import android.os.ParcelUuid;

import com.googlecode.android_scripting.Log;
import com.googlecode.android_scripting.facade.FacadeManager;
import com.googlecode.android_scripting.jsonrpc.RpcReceiver;
import com.googlecode.android_scripting.rpc.Rpc;
import com.googlecode.android_scripting.rpc.RpcDefault;
import com.googlecode.android_scripting.rpc.RpcParameter;

import java.util.ArrayList;
import java.util.List;

public class BluetoothHfpClientFacade extends RpcReceiver {
    static final ParcelUuid[] UUIDS = {
        BluetoothUuid.HFP_AG,
    };

    private final Service mService;
    private final BluetoothAdapter mBluetoothAdapter;

    private static boolean sIsHfpClientReady = false;
    private static BluetoothHeadsetClient sHfpClientProfile = null;

    public BluetoothHfpClientFacade(FacadeManager manager) {
        super(manager);
        mService = manager.getService();
        mBluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        mBluetoothAdapter.getProfileProxy(mService,
                new HfpClientServiceListener(),
                BluetoothProfile.HEADSET_CLIENT);
    }

    class HfpClientServiceListener implements BluetoothProfile.ServiceListener {
        @Override
        public void onServiceConnected(int profile, BluetoothProfile proxy) {
            sHfpClientProfile = (BluetoothHeadsetClient) proxy;
            sIsHfpClientReady = true;
        }

        @Override
        public void onServiceDisconnected(int profile) {
            sIsHfpClientReady = false;
        }
    }

    /**
     * Connect to HfpClient.
     * @param device - the BluetoothDevice object to connect Hfp client.
     * @return if the connection was successfull or not.
     */
    public Boolean hfpClientConnect(BluetoothDevice device) {
        if (sHfpClientProfile == null) return false;
        return sHfpClientProfile.connect(device);
    }

    /**
     * Disconnect from HfpClient.
     * @param device - the BluetoothDevice object to disconnect from Hfp client.
     * @return if the disconnection was successfull or not.
     */
    public Boolean hfpClientDisconnect(BluetoothDevice device) {
        if (sHfpClientProfile == null) return false;
        return sHfpClientProfile.disconnect(device);
    }

    /**
     * Is Hfp Client profile ready.
     * @return Hfp Client profile is ready or not.
     */
    @Rpc(description = "Is HfpClient profile ready.")
    public Boolean bluetoothHfpClientIsReady() {
        return sIsHfpClientReady;
    }

    /**
     * Set priority of the profile.
     * @param deviceStr - Mac address of a BT device.
     * @param priority - Priority that needs to be set.
     */
    @Rpc(description = "Set priority of the profile")
    public void bluetoothHfpClientSetPriority(
            @RpcParameter(name = "device",
                description = "Mac address of a BT device.") String deviceStr,
            @RpcParameter(name = "priority",
                description = "Priority that needs to be set.")
                    Integer priority) throws Exception {
        if (sHfpClientProfile == null) return;
        BluetoothDevice device =
                BluetoothFacade.getDevice(mBluetoothAdapter.getBondedDevices(),
                    deviceStr);
        Log.d("Changing priority of device " + device.getAlias()
                + " p: " + priority);
        sHfpClientProfile.setPriority(device, priority);
    }

    /**
     * Get priority of the profile.
     * @param deviceStr - Mac address of a BT device.
     * @return Priority of the device.
     */
    @Rpc(description = "Get priority of the profile")
    public Integer bluetoothHfpClientGetPriority(
            @RpcParameter(name = "device", description =
                    "Mac address of a BT device.") String deviceStr)
                    throws Exception {
        if (sHfpClientProfile == null) return BluetoothProfile.PRIORITY_UNDEFINED;
        BluetoothDevice device = BluetoothFacade.getDevice(
                mBluetoothAdapter.getBondedDevices(), deviceStr);
        return sHfpClientProfile.getPriority(device);
    }

    /**
     * Connect to an HFP Client device.
     * @param deviceStr - Name or MAC address of a bluetooth device.
     * @return Hfp Client was connected or not.
     */
    @Rpc(description = "Connect to an HFP Client device.")
    public Boolean bluetoothHfpClientConnect(
            @RpcParameter(name = "device",
                description = "Name or MAC address of a bluetooth device.")
                    String deviceStr)
                        throws Exception {
        if (sHfpClientProfile == null) return false;
        try {
            BluetoothDevice device = BluetoothFacade.getDevice(
                    BluetoothFacade.DiscoveredDevices, deviceStr);
            Log.d("Connecting to device " + device.getAlias());
            return hfpClientConnect(device);
        } catch (Exception e) {
            Log.e("bluetoothHfpClientConnect failed on getDevice "
                    + deviceStr + " with " + e);
            return false;
        }
    }

    /**
     * Disconnect an HFP Client device.
     * @param deviceStr - Name or MAC address of a bluetooth device.
     * @return Hfp Client was disconnected or not.
     */
    @Rpc(description = "Disconnect an HFP Client device.")
    public Boolean bluetoothHfpClientDisconnect(
            @RpcParameter(name = "device",
                description = "Name or MAC address of a device.")
                    String deviceStr) {
        if (sHfpClientProfile == null) return false;
        Log.d("Connected devices: " + sHfpClientProfile.getConnectedDevices());
        try {
            BluetoothDevice device = BluetoothFacade.getDevice(
                    sHfpClientProfile.getConnectedDevices(), deviceStr);
            return hfpClientDisconnect(device);
        } catch (Exception e) {
            // Do nothing since it is disconnect and this
            // function should force disconnect.
            Log.e("bluetoothHfpClientConnect getDevice failed " + e);
        }
        return false;
    }

    /**
     * Get all the devices connected through HFP Client.
     * @return List of all the devices connected through HFP Client.
     */
    @Rpc(description = "Get all the devices connected through HFP Client.")
    public List<BluetoothDevice> bluetoothHfpClientGetConnectedDevices() {
        if (sHfpClientProfile == null) return new ArrayList<BluetoothDevice>();
        return sHfpClientProfile.getConnectedDevices();
    }

    /**
     * Get the connection status of a device.
     * @param deviceID - Name or MAC address of a bluetooth device.
     * @return connection status of the device.
     */
    @Rpc(description = "Get the connection status of a device.")
    public Integer bluetoothHfpClientGetConnectionStatus(
            @RpcParameter(name = "deviceID",
                description = "Name or MAC address of a bluetooth device.")
                    String deviceID) {
        if (sHfpClientProfile == null) {
            return BluetoothProfile.STATE_DISCONNECTED;
        }
        List<BluetoothDevice> deviceList =
                sHfpClientProfile.getConnectedDevices();
        BluetoothDevice device;
        try {
            device = BluetoothFacade.getDevice(deviceList, deviceID);
        } catch (Exception e) {
            Log.e(e);
            return BluetoothProfile.STATE_DISCONNECTED;
        }
        return sHfpClientProfile.getConnectionState(device);
    }

    /**
     * Get the audio routing state of specified device.
     * @param deviceStr the Bluetooth MAC address of remote device
     * @return Audio State of the device.
     */
    @Rpc(description = "Get all the devices connected through HFP Client.")
    public Integer bluetoothHfpClientGetAudioState(
            @RpcParameter(name = "device",
                description = "MAC address of a bluetooth device.")
                String deviceStr) {
        if (sHfpClientProfile == null) return -1;
        BluetoothDevice device;
        try {
            device =  BluetoothFacade.getDevice(sHfpClientProfile.getConnectedDevices(), deviceStr);
        } catch (Exception e) {
            // Do nothing since it is disconnect and this function should force disconnect.
            Log.e("bluetoothHfpClientConnect getDevice failed " + e);
            return -1;
        }
        return sHfpClientProfile.getAudioState(device);
    }

    private BluetoothDevice getDevice(String deviceStr) {
        if (sHfpClientProfile == null) return null;
        BluetoothDevice device;
        try {
            device =  BluetoothFacade.getDevice(sHfpClientProfile.getConnectedDevices(), deviceStr);
        } catch (Exception e) {
            // Do nothing since it is disconnect and this function should force disconnect.
            Log.e("bluetoothHfpClientConnect getDevice failed " + e);
            return null;
        }
        return device;
    }

    /**
     * Starts Voice Recognition on remote device
     *
     * @param deviceStr the Bluetooth MAC address of remote device
     * @return True if command has been issued successfully
     */
    @Rpc(description = "Start Remote device Voice Recognition through HFP Client.")
    public boolean bluetoothHfpClientStartVoiceRecognition(
            @RpcParameter(name = "device",
                description = "MAC address of a bluetooth device.")
                    String deviceStr) {
        BluetoothDevice device = getDevice(deviceStr);
        if (device == null) return false;
        return sHfpClientProfile.startVoiceRecognition(device);
    }

    /**
     * Stops Voice Recognition in the remote device through Bluetooth HFP client
     *
     * @param deviceStr the Bluetooth MAC address of remote device
     * @return True if command has been issued successfully
     */
    @Rpc(description = "Stops Remote device Voice Recognition through HFP Client.")
    public boolean bluetoothHfpClientStopVoiceRecognition(
            @RpcParameter(name = "device",
                description = "MAC address of a bluetooth device.")
                    String deviceStr) {
        BluetoothDevice device = getDevice(deviceStr);
        if (device == null) return false;
        return sHfpClientProfile.stopVoiceRecognition(device);
    }

    /**
     * Initiates a connection of audio channel.
     *
     * It setup SCO channel with remote connected Handsfree Audio Gateway device.
     *
     * @param deviceStr the Bluetooth MAC address of remote device
     * @return True if command has been issued successfully
     */
    @Rpc(description = "Initiates a connection of audio channel.")
    public boolean bluetoothHfpClientConnectAudio(
            @RpcParameter(name = "device",
                description = "MAC address of a bluetooth device.")
                String deviceStr) {
        BluetoothDevice device = getDevice(deviceStr);
        if (device == null) return false;
        return sHfpClientProfile.connectAudio(device);
    }

    /**
     * Dials a call in the remote device through Bluetooth HFP Client
     *
     * The last number dial will be placed if the number is an empty string
     *
     * @param deviceStr the Bluetooth MAC address of remote device
     * @param number phone number to dial, the value of null or empty string for last number redial
     * @return The string of <code>{@link BluetoothHeadsetClientCall} call</code> or null if no
     *         device was not found.
     */
    @Rpc(description = "Dials a call in the remote device through HFP Client.")
    public String bluetoothHfpClientDial(
            @RpcParameter(name = "device",
                description = "MAC address of a bluetooth device.") String deviceStr,
            @RpcParameter(name = "phone_number", description =
                "phone number to dial, default for last number redial")
                @RpcDefault("") String number) {
        BluetoothDevice device = getDevice(deviceStr);
        if (device == null) return null;
        return sHfpClientProfile.dial(device, number).toString(true);
    }

    /**
     * Disconnects audio channel.
     *
     * It tears down the SCO channel from remote AuG device.
     *
     * @param deviceStr the Bluetooth MAC address of remote device
     * @return True if command has been issued successfully
     */
    @Rpc(description = "Disconnects audio channel.")
    public boolean bluetoothHfpClientDisconnectAudio(
            @RpcParameter(name = "device",
                description = "MAC address of a bluetooth device.")
                String deviceStr) {
        BluetoothDevice device = getDevice(deviceStr);
        if (device == null) return false;
        return sHfpClientProfile.disconnectAudio(device);
    }

    /**
     * Accepts a call in the remote device through Bluetooth HFP Client
     *
     * @param deviceStr the Bluetooth MAC address of remote device
     * @return True if command has been issued successfully
     */
    @Rpc(description = "Accepts a call in the remote device through HFP Client.")
    public boolean bluetoothHfpClientAcceptCall(
            @RpcParameter(name = "device",
                description = "MAC address of a bluetooth device.")
                    String deviceStr) {
        BluetoothDevice device = getDevice(deviceStr);
        if (device == null) return false;
        return sHfpClientProfile.acceptCall(device, BluetoothHeadsetClient.CALL_ACCEPT_NONE);
    }

    /**
     * Terminates all calls in the remote device through Bluetooth HFP Client
     *
     * @param deviceStr the Bluetooth MAC address of remote device
     * @return True if command has been issued successfully
     */
    @Rpc(description = "Terminates all calls in the remote device through HFP Client.")
    public boolean bluetoothHfpClientTerminateAllCalls(
            @RpcParameter(name = "device",
                description = "MAC address of a bluetooth device.")
                    String deviceStr) {
        BluetoothDevice device = getDevice(deviceStr);
        if (device == null) return false;
        return sHfpClientProfile.terminateCall(device, null);
    }

    /**
     * Rejects a call in the remote device through Bluetooth HFP Client
     *
     * @param deviceStr the Bluetooth MAC address of remote device
     * @return True if command has been issued successfully
     */
    @Rpc(description = "Rejects a call in the remote device through HFP Client.")
    public boolean bluetoothHfpClientRejectCall(
            @RpcParameter(name = "device",
                description = "MAC address of a bluetooth device.")
                    String deviceStr) {
        BluetoothDevice device = getDevice(deviceStr);
        if (device == null) return false;
        return sHfpClientProfile.rejectCall(device);
    }

    @Override
    public void shutdown() {
    }
}
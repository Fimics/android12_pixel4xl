/*
 * Copyright (C) 2021 The Android Open Source Project
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

package com.android.car.audio;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import android.util.SparseArray;

import com.google.common.collect.ImmutableList;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

/**
 * Class to build mock volume group
 */
public final class VolumeGroupBuilder {

    private SparseArray<String> mDeviceAddresses = new SparseArray<>();
    private boolean mIsMuted;

    /**
     * Add devices address for context
     */
    public VolumeGroupBuilder addDeviceAddressAndContexts(@CarAudioContext.AudioContext int context,
            String address) {
        mDeviceAddresses.put(context, address);
        return this;
    }

    /**
     * Sets volume group is muted
     */
    public VolumeGroupBuilder setIsMuted(boolean isMuted) {
        mIsMuted = isMuted;
        return this;
    }


    /**
     * Builds car volume group
     */
    public CarVolumeGroup build() {
        CarVolumeGroup carVolumeGroup = mock(CarVolumeGroup.class);
        Map<String, ArrayList<Integer>> addressToContexts = new HashMap<>();
        int[] contexts = new int[mDeviceAddresses.size()];

        for (int index = 0; index < mDeviceAddresses.size(); index++) {
            int context = mDeviceAddresses.keyAt(index);
            String address = mDeviceAddresses.get(context);
            when(carVolumeGroup.getAddressForContext(context)).thenReturn(address);
            if (!addressToContexts.containsKey(address)) {
                addressToContexts.put(address, new ArrayList<>());
            }
            addressToContexts.get(address).add(context);
            contexts[index] = context;
        }

        when(carVolumeGroup.getContexts()).thenReturn(contexts);

        addressToContexts.forEach((address, array) ->
                when(carVolumeGroup.getContextsForAddress(address))
                .thenReturn(ImmutableList.copyOf(array)));

        when(carVolumeGroup.getAddresses())
                .thenReturn(ImmutableList.copyOf(addressToContexts.keySet()));

        when(carVolumeGroup.isMuted()).thenReturn(mIsMuted);
        return carVolumeGroup;
    }
}

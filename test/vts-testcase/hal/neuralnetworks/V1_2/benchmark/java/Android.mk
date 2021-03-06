# Copyright (C) 2019 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_PACKAGE_NAME := VtsHalNeuralnetworksV1_2BenchmarkTestCases
LOCAL_LICENSE_KINDS := SPDX-license-identifier-Apache-2.0
LOCAL_LICENSE_CONDITIONS := notice

# Don't include this package in any target
LOCAL_MODULE_TAGS := optional
# And when built explicitly put it in the data partition
LOCAL_MODULE_PATH := $(TARGET_OUT_DATA_APPS)

# Include both the 32 and 64 bit versions
LOCAL_MULTILIB := both

# Tag this module as a cts test artifact
LOCAL_COMPATIBILITY_SUITE := vts vts10

LOCAL_STATIC_JAVA_LIBRARIES := androidx.test.rules android.hidl.manager-V1.2-java \
    compatibility-device-util-axt ctstestrunner-axt junit NeuralNetworksApiBenchmark_Lib
LOCAL_JNI_SHARED_LIBRARIES := libnnbenchmark_jni

# Disable dexpreopt and <uses-library> check for test.
LOCAL_ENFORCE_USES_LIBRARIES := false
LOCAL_DEX_PREOPT := false

LOCAL_SRC_FILES := $(call all-java-files-under, src)
LOCAL_ASSET_DIR := test/mlts/models/assets

LOCAL_SDK_VERSION := system_current

include $(BUILD_CTS_PACKAGE)

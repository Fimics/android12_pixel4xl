// Copyright (C) 2020 The Android Open Source Project
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#pragma once

// clang-format off
#include PATH(device/google/atv/audio_proxy/AUDIO_PROXY_FILE_VERSION/IBusDevice.h)
// clang-format on
#include "DummyOutputStream.h"

namespace audio_proxy {
namespace service {

using ::android::hardware::hidl_bitfield;
using ::android::hardware::Return;
using ::device::google::atv::audio_proxy::AUDIO_PROXY_CPP_VERSION::IBusDevice;
using namespace ::android::hardware::audio::common::CPP_VERSION;
using namespace ::android::hardware::audio::CPP_VERSION;

class DummyBusDevice : public IBusDevice {
 public:
  // Methods from IBusDevice:
  Return<void> openOutputStream(int32_t ioHandle, const DeviceAddress &device,
                                const AudioConfig &config,
                                hidl_bitfield<AudioOutputFlag> flags,
                                const SourceMetadata &sourceMetadata,
                                openOutputStream_cb _hidl_cb) override;
};

} // namespace service
} // namespace audio_proxy

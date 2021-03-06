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

#ifndef WIFICOND_TEST_MOCK_CLIENT_INTERFACE_IMPL_H_
#define WIFICOND_TEST_MOCK_CLIENT_INTERFACE_IMPL_H_

#include <gmock/gmock.h>

#include "wificond/client_interface_impl.h"

namespace android {

namespace wificond {

class MockClientInterfaceImpl : public ClientInterfaceImpl {
 public:
  MockClientInterfaceImpl(
      android::wifi_system::InterfaceTool*,
      NetlinkUtils*,
      ScanUtils*);
  ~MockClientInterfaceImpl() override = default;

  MOCK_CONST_METHOD0(IsAssociated, bool());

  MOCK_CONST_METHOD0(GetBandInfo, BandInfo());

};  // class MockClientInterfaceImpl

}  // namespace wificond
}  // namespace android

#endif  // WIFICOND_TEST_MOCK_CLIENT_INTERFACE_IMPL_H_

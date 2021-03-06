/*
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

#pragma once

#include <array>
#include <optional>
#include <string>

namespace android::hardware::automotive::utils {

using PropertyList = std::initializer_list<std::string>;

struct VsockConnectionInfo {
    unsigned cid = 0;
    unsigned port = 0;

    static std::optional<VsockConnectionInfo> fromRoPropertyStore(const PropertyList& cid_props,
                                                                  const PropertyList& port_props);

    std::string str() const;
};

}  // namespace android::hardware::automotive::utils

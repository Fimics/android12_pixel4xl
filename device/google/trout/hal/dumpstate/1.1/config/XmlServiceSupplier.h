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

#include "ServiceSupplier.h"
#include "config/dumpstate_hal_configuration_V1_0.h"

using dumpstate::hal::configuration::V1_0::DumpstateHalConfiguration;

class XmlServiceSupplier : public ServiceSupplier {
  public:
    static std::optional<XmlServiceSupplier> fromFile(const std::string& path);
    static std::optional<XmlServiceSupplier> fromBuffer(const std::string& buffer);

    std::optional<ServiceDescriptor> GetSystemLogsService() const override;
    std::vector<ServiceDescriptor> GetServices() const override;

  private:
    explicit XmlServiceSupplier(const DumpstateHalConfiguration& cfg);

    std::optional<ServiceDescriptor> mSystemLogs;
    std::vector<ServiceDescriptor> mServices;
};

#
# Copyright (C) 2020 The Android Open-Source Project
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
#

# Contents of this file were copied from device/google/sunfish/sunfish/BoardConfig.mk,
# except for:
#
# * TARGET_SCREEN_DENSITY is scaled down by 1.75x


TARGET_BOOTLOADER_BOARD_NAME := bramble
TARGET_RECOVERY_UI_MARGIN_HEIGHT := 165
USES_DEVICE_GOOGLE_BRAMBLE := true

include device/google/redbull/BoardConfig-common.mk

# Testing related defines
#BOARD_PERFSETUP_SCRIPT := platform_testing/scripts/perf-setup/b5-setup.sh

-include vendor/google_devices/$(TARGET_BOOTLOADER_BOARD_NAME)/proprietary/BoardConfigVendor.mk

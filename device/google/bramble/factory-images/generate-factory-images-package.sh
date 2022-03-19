#!/bin/sh

# Copyright 2020 The Android Open Source Project
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

source ../../../common/clear-factory-images-variables.sh
BUILD=6291635
DEVICE=bramble
PRODUCT=bramble
VERSION=rd1a.200312.002
SRCPREFIX=signed-
BOOTLOADER=b5-0.2-6218156
RADIO=g7250-00014-200305-B-6264959
source ../../../common/generate-factory-images-common.sh

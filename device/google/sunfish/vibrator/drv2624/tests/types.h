/*
 * Copyright (C) 2019 The Android Open Source Project
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
#ifndef ANDROID_HARDWARE_VIBRATOR_TEST_TYPES_H
#define ANDROID_HARDWARE_VIBRATOR_TEST_TYPES_H

#include <android/hardware/vibrator/1.3/IVibrator.h>

using EffectAmplitude = uint8_t;
using EffectDuration = uint32_t;
using EffectSequence = std::tuple<std::string, uint8_t>;
using EffectTuple = std::tuple<::android::hardware::vibrator::V1_3::Effect,
                               ::android::hardware::vibrator::V1_0::EffectStrength>;

#endif  // ANDROID_HARDWARE_VIBRATOR_TEST_TYPES_H

/*
 * Copyright (C) 2018 The Android Open Source Project
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

#ifndef LIBTEXTCLASSIFIER_ANNOTATOR_DATETIME_UTILS_H_
#define LIBTEXTCLASSIFIER_ANNOTATOR_DATETIME_UTILS_H_

#include <vector>

#include "annotator/types.h"
#include "utils/base/integral_types.h"

namespace libtextclassifier3 {

// Generate alternative interpretations when datetime is ambiguous e.g. '9:45'
// has hour:9 and minute:45 will be resolve to 9:45 AM & 9:45 PM.
void FillInterpretations(const DatetimeParsedData& parse,
                         const DatetimeGranularity& granularity,
                         std::vector<DatetimeParsedData>* interpretations);

// Logic to decide if XX will be 20XX or 19XX
int GetAdjustedYear(const int parsed_year);
}  // namespace libtextclassifier3

#endif  // LIBTEXTCLASSIFIER_ANNOTATOR_DATETIME_UTILS_H_

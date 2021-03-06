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

// Auxiliary methods for using rules.

#ifndef LIBTEXTCLASSIFIER_UTILS_GRAMMAR_RULES_UTILS_H_
#define LIBTEXTCLASSIFIER_UTILS_GRAMMAR_RULES_UTILS_H_

#include <vector>

#include "utils/grammar/rules_generated.h"
#include "utils/i18n/locale.h"

namespace libtextclassifier3::grammar {

// Parses the locales of each rules shard.
std::vector<std::vector<Locale>> ParseRulesLocales(const RulesSet* rules);

// Selects rules shards that match on any locale.
std::vector<const grammar::RulesSet_::Rules*> SelectLocaleMatchingShards(
    const RulesSet* rules,
    const std::vector<std::vector<Locale>>& shard_locales,
    const std::vector<Locale>& locales);

}  // namespace libtextclassifier3::grammar

#endif  // LIBTEXTCLASSIFIER_UTILS_GRAMMAR_RULES_UTILS_H_

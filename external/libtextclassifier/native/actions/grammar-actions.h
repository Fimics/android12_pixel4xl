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

#ifndef LIBTEXTCLASSIFIER_ACTIONS_GRAMMAR_ACTIONS_H_
#define LIBTEXTCLASSIFIER_ACTIONS_GRAMMAR_ACTIONS_H_

#include <memory>
#include <vector>

#include "actions/actions_model_generated.h"
#include "actions/types.h"
#include "utils/flatbuffers/mutable.h"
#include "utils/grammar/analyzer.h"
#include "utils/grammar/evaluated-derivation.h"
#include "utils/grammar/text-context.h"
#include "utils/i18n/locale.h"
#include "utils/tokenizer.h"
#include "utils/utf8/unilib.h"

namespace libtextclassifier3 {

// Grammar backed actions suggestions.
class GrammarActions {
 public:
  explicit GrammarActions(const UniLib* unilib,
                          const RulesModel_::GrammarRules* grammar_rules,
                          const MutableFlatbufferBuilder* entity_data_builder,
                          const std::string& smart_reply_action_type);

  // Suggests actions for a conversation from a message stream.
  bool SuggestActions(const Conversation& conversation,
                      std::vector<ActionSuggestion>* result) const;

 private:
  // Creates action suggestions from a grammar match result.
  bool InstantiateActionsFromMatch(const grammar::TextContext& text_context,
                                   int message_index,
                                   const grammar::Derivation& derivation,
                                   std::vector<ActionSuggestion>* result) const;

  const UniLib& unilib_;
  const RulesModel_::GrammarRules* grammar_rules_;
  const std::unique_ptr<Tokenizer> tokenizer_;
  const MutableFlatbufferBuilder* entity_data_builder_;
  const grammar::Analyzer analyzer_;
  const std::string smart_reply_action_type_;
};

}  // namespace libtextclassifier3

#endif  // LIBTEXTCLASSIFIER_ACTIONS_GRAMMAR_ACTIONS_H_

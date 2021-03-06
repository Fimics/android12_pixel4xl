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

#include "annotator/feature-processor.h"

#include <iterator>
#include <set>
#include <vector>

#include "utils/base/logging.h"
#include "utils/strings/utf8.h"
#include "utils/utf8/unicodetext.h"

namespace libtextclassifier3 {

namespace internal {

Tokenizer BuildTokenizer(const FeatureProcessorOptions* options,
                         const UniLib* unilib) {
  std::vector<const TokenizationCodepointRange*> codepoint_config;
  if (options->tokenization_codepoint_config() != nullptr) {
    codepoint_config.insert(codepoint_config.end(),
                            options->tokenization_codepoint_config()->begin(),
                            options->tokenization_codepoint_config()->end());
  }
  std::vector<const CodepointRange*> internal_codepoint_config;
  if (options->internal_tokenizer_codepoint_ranges() != nullptr) {
    internal_codepoint_config.insert(
        internal_codepoint_config.end(),
        options->internal_tokenizer_codepoint_ranges()->begin(),
        options->internal_tokenizer_codepoint_ranges()->end());
  }
  const bool tokenize_on_script_change =
      options->tokenization_codepoint_config() != nullptr &&
      options->tokenize_on_script_change();
  return Tokenizer(options->tokenization_type(), unilib, codepoint_config,
                   internal_codepoint_config, tokenize_on_script_change,
                   options->icu_preserve_whitespace_tokens());
}

TokenFeatureExtractorOptions BuildTokenFeatureExtractorOptions(
    const FeatureProcessorOptions* const options) {
  TokenFeatureExtractorOptions extractor_options;

  extractor_options.num_buckets = options->num_buckets();
  if (options->chargram_orders() != nullptr) {
    for (int order : *options->chargram_orders()) {
      extractor_options.chargram_orders.push_back(order);
    }
  }
  extractor_options.max_word_length = options->max_word_length();
  extractor_options.extract_case_feature = options->extract_case_feature();
  extractor_options.unicode_aware_features = options->unicode_aware_features();
  extractor_options.extract_selection_mask_feature =
      options->extract_selection_mask_feature();
  if (options->regexp_feature() != nullptr) {
    for (const auto& regexp_feature : *options->regexp_feature()) {
      extractor_options.regexp_features.push_back(regexp_feature->str());
    }
  }
  extractor_options.remap_digits = options->remap_digits();
  extractor_options.lowercase_tokens = options->lowercase_tokens();

  if (options->allowed_chargrams() != nullptr) {
    for (const auto& chargram : *options->allowed_chargrams()) {
      extractor_options.allowed_chargrams.insert(chargram->str());
    }
  }
  return extractor_options;
}

void SplitTokensOnSelectionBoundaries(const CodepointSpan& selection,
                                      std::vector<Token>* tokens) {
  for (auto it = tokens->begin(); it != tokens->end(); ++it) {
    const UnicodeText token_word =
        UTF8ToUnicodeText(it->value, /*do_copy=*/false);

    auto last_start = token_word.begin();
    int last_start_index = it->start;
    std::vector<UnicodeText::const_iterator> split_points;

    // Selection start split point.
    if (selection.first > it->start && selection.first < it->end) {
      std::advance(last_start, selection.first - last_start_index);
      split_points.push_back(last_start);
      last_start_index = selection.first;
    }

    // Selection end split point.
    if (selection.second > it->start && selection.second < it->end) {
      std::advance(last_start, selection.second - last_start_index);
      split_points.push_back(last_start);
    }

    if (!split_points.empty()) {
      // Add a final split for the rest of the token unless it's been all
      // consumed already.
      if (split_points.back() != token_word.end()) {
        split_points.push_back(token_word.end());
      }

      std::vector<Token> replacement_tokens;
      last_start = token_word.begin();
      int current_pos = it->start;
      for (const auto& split_point : split_points) {
        Token new_token(token_word.UTF8Substring(last_start, split_point),
                        current_pos,
                        current_pos + std::distance(last_start, split_point));

        last_start = split_point;
        current_pos = new_token.end;

        replacement_tokens.push_back(new_token);
      }

      it = tokens->erase(it);
      it = tokens->insert(it, replacement_tokens.begin(),
                          replacement_tokens.end());
      std::advance(it, replacement_tokens.size() - 1);
    }
  }
}

}  // namespace internal

void FeatureProcessor::StripTokensFromOtherLines(
    const std::string& context, const CodepointSpan& span,
    std::vector<Token>* tokens) const {
  const UnicodeText context_unicode = UTF8ToUnicodeText(context,
                                                        /*do_copy=*/false);
  const auto [span_begin, span_end] =
      CodepointSpanToUnicodeTextRange(context_unicode, span);
  StripTokensFromOtherLines(context_unicode, span_begin, span_end, span,
                            tokens);
}

void FeatureProcessor::StripTokensFromOtherLines(
    const UnicodeText& context_unicode,
    const UnicodeText::const_iterator& span_begin,
    const UnicodeText::const_iterator& span_end, const CodepointSpan& span,
    std::vector<Token>* tokens) const {
  std::vector<UnicodeTextRange> lines =
      SplitContext(context_unicode, options_->use_pipe_character_for_newline());

  for (const UnicodeTextRange& line : lines) {
    // Find the line that completely contains the span.
    if (line.first <= span_begin && line.second >= span_end) {
      const CodepointIndex last_line_begin_index =
          std::distance(context_unicode.begin(), line.first);
      const CodepointIndex last_line_end_index =
          last_line_begin_index + std::distance(line.first, line.second);

      for (auto token = tokens->begin(); token != tokens->end();) {
        if (token->start >= last_line_begin_index &&
            token->end <= last_line_end_index) {
          ++token;
        } else {
          token = tokens->erase(token);
        }
      }
    }
  }
}

std::string FeatureProcessor::GetDefaultCollection() const {
  if (options_->default_collection() < 0 ||
      options_->collections() == nullptr ||
      options_->default_collection() >= options_->collections()->size()) {
    TC3_LOG(ERROR)
        << "Invalid or missing default collection. Returning empty string.";
    return "";
  }
  return (*options_->collections())[options_->default_collection()]->str();
}

std::vector<Token> FeatureProcessor::Tokenize(const std::string& text) const {
  return tokenizer_.Tokenize(text);
}

std::vector<Token> FeatureProcessor::Tokenize(
    const UnicodeText& text_unicode) const {
  return tokenizer_.Tokenize(text_unicode);
}

bool FeatureProcessor::LabelToSpan(const int label,
                                   const VectorSpan<Token>& tokens,
                                   CodepointSpan* span) const {
  if (tokens.size() != GetNumContextTokens()) {
    return false;
  }

  TokenSpan token_span;
  if (!LabelToTokenSpan(label, &token_span)) {
    return false;
  }

  const int result_begin_token_index = token_span.first;
  const Token& result_begin_token =
      tokens[options_->context_size() - result_begin_token_index];
  const int result_begin_codepoint = result_begin_token.start;
  const int result_end_token_index = token_span.second;
  const Token& result_end_token =
      tokens[options_->context_size() + result_end_token_index];
  const int result_end_codepoint = result_end_token.end;

  if (result_begin_codepoint == kInvalidIndex ||
      result_end_codepoint == kInvalidIndex) {
    *span = CodepointSpan::kInvalid;
  } else {
    const UnicodeText token_begin_unicode =
        UTF8ToUnicodeText(result_begin_token.value, /*do_copy=*/false);
    UnicodeText::const_iterator token_begin = token_begin_unicode.begin();
    const UnicodeText token_end_unicode =
        UTF8ToUnicodeText(result_end_token.value, /*do_copy=*/false);
    UnicodeText::const_iterator token_end = token_end_unicode.end();

    const int begin_ignored = CountIgnoredSpanBoundaryCodepoints(
        token_begin, token_begin_unicode.end(),
        /*count_from_beginning=*/true);
    const int end_ignored =
        CountIgnoredSpanBoundaryCodepoints(token_end_unicode.begin(), token_end,
                                           /*count_from_beginning=*/false);
    // In case everything would be stripped, set the span to the original
    // beginning and zero length.
    if (begin_ignored == (result_end_codepoint - result_begin_codepoint)) {
      *span = {result_begin_codepoint, result_begin_codepoint};
    } else {
      *span = CodepointSpan(result_begin_codepoint + begin_ignored,
                            result_end_codepoint - end_ignored);
    }
  }
  return true;
}

bool FeatureProcessor::LabelToTokenSpan(const int label,
                                        TokenSpan* token_span) const {
  if (label >= 0 && label < label_to_selection_.size()) {
    *token_span = label_to_selection_[label];
    return true;
  } else {
    return false;
  }
}

bool FeatureProcessor::SpanToLabel(const CodepointSpan& span,
                                   const std::vector<Token>& tokens,
                                   int* label) const {
  if (tokens.size() != GetNumContextTokens()) {
    return false;
  }

  const int click_position =
      options_->context_size();  // Click is always in the middle.
  const int padding = options_->context_size() - options_->max_selection_span();

  int span_left = 0;
  for (int i = click_position - 1; i >= padding; i--) {
    if (tokens[i].start != kInvalidIndex && tokens[i].end > span.first) {
      ++span_left;
    } else {
      break;
    }
  }

  int span_right = 0;
  for (int i = click_position + 1; i < tokens.size() - padding; ++i) {
    if (tokens[i].end != kInvalidIndex && tokens[i].start < span.second) {
      ++span_right;
    } else {
      break;
    }
  }

  // Check that the spanned tokens cover the whole span.
  bool tokens_match_span;
  const CodepointIndex tokens_start = tokens[click_position - span_left].start;
  const CodepointIndex tokens_end = tokens[click_position + span_right].end;
  if (options_->snap_label_span_boundaries_to_containing_tokens()) {
    tokens_match_span = tokens_start <= span.first && tokens_end >= span.second;
  } else {
    const UnicodeText token_left_unicode = UTF8ToUnicodeText(
        tokens[click_position - span_left].value, /*do_copy=*/false);
    const UnicodeText token_right_unicode = UTF8ToUnicodeText(
        tokens[click_position + span_right].value, /*do_copy=*/false);

    UnicodeText::const_iterator span_begin = token_left_unicode.begin();
    UnicodeText::const_iterator span_end = token_right_unicode.end();

    const int num_punctuation_start = CountIgnoredSpanBoundaryCodepoints(
        span_begin, token_left_unicode.end(), /*count_from_beginning=*/true);
    const int num_punctuation_end = CountIgnoredSpanBoundaryCodepoints(
        token_right_unicode.begin(), span_end,
        /*count_from_beginning=*/false);

    tokens_match_span = tokens_start <= span.first &&
                        tokens_start + num_punctuation_start >= span.first &&
                        tokens_end >= span.second &&
                        tokens_end - num_punctuation_end <= span.second;
  }

  if (tokens_match_span) {
    *label = TokenSpanToLabel({span_left, span_right});
  } else {
    *label = kInvalidLabel;
  }

  return true;
}

int FeatureProcessor::TokenSpanToLabel(const TokenSpan& token_span) const {
  auto it = selection_to_label_.find(token_span);
  if (it != selection_to_label_.end()) {
    return it->second;
  } else {
    return kInvalidLabel;
  }
}

TokenSpan CodepointSpanToTokenSpan(const std::vector<Token>& selectable_tokens,
                                   const CodepointSpan& codepoint_span,
                                   bool snap_boundaries_to_containing_tokens) {
  const int codepoint_start = codepoint_span.first;
  const int codepoint_end = codepoint_span.second;

  TokenIndex start_token = kInvalidIndex;
  TokenIndex end_token = kInvalidIndex;
  for (int i = 0; i < selectable_tokens.size(); ++i) {
    bool is_token_in_span;
    if (snap_boundaries_to_containing_tokens) {
      is_token_in_span = codepoint_start < selectable_tokens[i].end &&
                         codepoint_end > selectable_tokens[i].start;
    } else {
      is_token_in_span = codepoint_start <= selectable_tokens[i].start &&
                         codepoint_end >= selectable_tokens[i].end;
    }
    if (is_token_in_span && !selectable_tokens[i].is_padding) {
      if (start_token == kInvalidIndex) {
        start_token = i;
      }
      end_token = i + 1;
    }
  }
  return {start_token, end_token};
}

CodepointSpan TokenSpanToCodepointSpan(
    const std::vector<Token>& selectable_tokens, const TokenSpan& token_span) {
  return {selectable_tokens[token_span.first].start,
          selectable_tokens[token_span.second - 1].end};
}

UnicodeTextRange CodepointSpanToUnicodeTextRange(
    const UnicodeText& unicode_text, const CodepointSpan& span) {
  auto begin = unicode_text.begin();
  if (span.first > 0) {
    std::advance(begin, span.first);
  }
  auto end = unicode_text.begin();
  if (span.second > 0) {
    std::advance(end, span.second);
  }
  return {begin, end};
}

namespace {

// Finds a single token that completely contains the given span.
int FindTokenThatContainsSpan(const std::vector<Token>& selectable_tokens,
                              const CodepointSpan& codepoint_span) {
  const int codepoint_start = codepoint_span.first;
  const int codepoint_end = codepoint_span.second;

  for (int i = 0; i < selectable_tokens.size(); ++i) {
    if (codepoint_start >= selectable_tokens[i].start &&
        codepoint_end <= selectable_tokens[i].end) {
      return i;
    }
  }
  return kInvalidIndex;
}

}  // namespace

namespace internal {

int CenterTokenFromClick(const CodepointSpan& span,
                         const std::vector<Token>& selectable_tokens) {
  const TokenSpan token_span =
      CodepointSpanToTokenSpan(selectable_tokens, span);
  int range_begin = token_span.first;
  int range_end = token_span.second;

  // If no exact match was found, try finding a token that completely contains
  // the click span. This is useful e.g. when Android builds the selection
  // using ICU tokenization, and ends up with only a portion of our space-
  // separated token. E.g. for "(857)" Android would select "857".
  if (range_begin == kInvalidIndex || range_end == kInvalidIndex) {
    int token_index = FindTokenThatContainsSpan(selectable_tokens, span);
    if (token_index != kInvalidIndex) {
      range_begin = token_index;
      range_end = token_index + 1;
    }
  }

  // We only allow clicks that are exactly 1 selectable token.
  if (range_end - range_begin == 1) {
    return range_begin;
  } else {
    return kInvalidIndex;
  }
}

int CenterTokenFromMiddleOfSelection(
    const CodepointSpan& span, const std::vector<Token>& selectable_tokens) {
  const TokenSpan token_span =
      CodepointSpanToTokenSpan(selectable_tokens, span);
  const int range_begin = token_span.first;
  const int range_end = token_span.second;

  // Center the clicked token in the selection range.
  if (range_begin != kInvalidIndex && range_end != kInvalidIndex) {
    return (range_begin + range_end - 1) / 2;
  } else {
    return kInvalidIndex;
  }
}

}  // namespace internal

int FeatureProcessor::FindCenterToken(const CodepointSpan& span,
                                      const std::vector<Token>& tokens) const {
  if (options_->center_token_selection_method() ==
      FeatureProcessorOptions_::
          CenterTokenSelectionMethod_CENTER_TOKEN_FROM_CLICK) {
    return internal::CenterTokenFromClick(span, tokens);
  } else if (options_->center_token_selection_method() ==
             FeatureProcessorOptions_::
                 CenterTokenSelectionMethod_CENTER_TOKEN_MIDDLE_OF_SELECTION) {
    return internal::CenterTokenFromMiddleOfSelection(span, tokens);
  } else if (options_->center_token_selection_method() ==
             FeatureProcessorOptions_::
                 CenterTokenSelectionMethod_DEFAULT_CENTER_TOKEN_METHOD) {
    // TODO(zilka): Remove once we have new models on the device.
    // It uses the fact that sharing model use
    // split_tokens_on_selection_boundaries and selection not. So depending on
    // this we select the right way of finding the click location.
    if (!options_->split_tokens_on_selection_boundaries()) {
      // SmartSelection model.
      return internal::CenterTokenFromClick(span, tokens);
    } else {
      // SmartSharing model.
      return internal::CenterTokenFromMiddleOfSelection(span, tokens);
    }
  } else {
    TC3_LOG(ERROR) << "Invalid center token selection method.";
    return kInvalidIndex;
  }
}

bool FeatureProcessor::SelectionLabelSpans(
    const VectorSpan<Token> tokens,
    std::vector<CodepointSpan>* selection_label_spans) const {
  for (int i = 0; i < label_to_selection_.size(); ++i) {
    CodepointSpan span = CodepointSpan::kInvalid;
    if (!LabelToSpan(i, tokens, &span)) {
      TC3_LOG(ERROR) << "Could not convert label to span: " << i;
      return false;
    }
    selection_label_spans->push_back(span);
  }
  return true;
}

bool FeatureProcessor::SelectionLabelRelativeTokenSpans(
    std::vector<TokenSpan>* selection_label_relative_token_spans) const {
  selection_label_relative_token_spans->assign(label_to_selection_.begin(),
                                               label_to_selection_.end());
  return true;
}

void FeatureProcessor::PrepareIgnoredSpanBoundaryCodepoints() {
  if (options_->ignored_span_boundary_codepoints() != nullptr) {
    for (const int codepoint : *options_->ignored_span_boundary_codepoints()) {
      ignored_span_boundary_codepoints_.insert(codepoint);
    }
  }
}

int FeatureProcessor::CountIgnoredSpanBoundaryCodepoints(
    const UnicodeText::const_iterator& span_start,
    const UnicodeText::const_iterator& span_end,
    bool count_from_beginning) const {
  if (span_start == span_end) {
    return 0;
  }

  UnicodeText::const_iterator it;
  UnicodeText::const_iterator it_last;
  if (count_from_beginning) {
    it = span_start;
    it_last = span_end;
    // We can assume that the string is non-zero length because of the check
    // above, thus the decrement is always valid here.
    --it_last;
  } else {
    it = span_end;
    it_last = span_start;
    // We can assume that the string is non-zero length because of the check
    // above, thus the decrement is always valid here.
    --it;
  }

  // Move until we encounter a non-ignored character.
  int num_ignored = 0;
  while (ignored_span_boundary_codepoints_.find(*it) !=
         ignored_span_boundary_codepoints_.end()) {
    ++num_ignored;

    if (it == it_last) {
      break;
    }

    if (count_from_beginning) {
      ++it;
    } else {
      --it;
    }
  }

  return num_ignored;
}

namespace {

void FindSubstrings(const UnicodeText& t, const std::set<char32>& codepoints,
                    std::vector<UnicodeTextRange>* ranges) {
  UnicodeText::const_iterator start = t.begin();
  UnicodeText::const_iterator curr = start;
  UnicodeText::const_iterator end = t.end();
  for (; curr != end; ++curr) {
    if (codepoints.find(*curr) != codepoints.end()) {
      if (start != curr) {
        ranges->push_back(std::make_pair(start, curr));
      }
      start = curr;
      ++start;
    }
  }
  if (start != end) {
    ranges->push_back(std::make_pair(start, end));
  }
}

}  // namespace

std::vector<UnicodeTextRange> FeatureProcessor::SplitContext(
    const UnicodeText& context_unicode,
    const bool use_pipe_character_for_newline) const {
  std::vector<UnicodeTextRange> lines;
  std::set<char32> codepoints{'\n'};
  if (use_pipe_character_for_newline) {
    codepoints.insert('|');
  }
  FindSubstrings(context_unicode, codepoints, &lines);
  return lines;
}

CodepointSpan FeatureProcessor::StripBoundaryCodepoints(
    const std::string& context, const CodepointSpan& span) const {
  const UnicodeText context_unicode =
      UTF8ToUnicodeText(context, /*do_copy=*/false);
  return StripBoundaryCodepoints(context_unicode, span);
}

CodepointSpan FeatureProcessor::StripBoundaryCodepoints(
    const UnicodeText& context_unicode, const CodepointSpan& span) const {
  if (context_unicode.empty() || !span.IsValid() || span.IsEmpty()) {
    return span;
  }

  const auto [span_begin, span_end] =
      CodepointSpanToUnicodeTextRange(context_unicode, span);

  return StripBoundaryCodepoints(span_begin, span_end, span);
}

CodepointSpan FeatureProcessor::StripBoundaryCodepoints(
    const UnicodeText::const_iterator& span_begin,
    const UnicodeText::const_iterator& span_end,
    const CodepointSpan& span) const {
  if (!span.IsValid() || span.IsEmpty() || span_begin == span_end) {
    return span;
  }

  const int start_offset = CountIgnoredSpanBoundaryCodepoints(
      span_begin, span_end, /*count_from_beginning=*/true);
  const int end_offset = CountIgnoredSpanBoundaryCodepoints(
      span_begin, span_end, /*count_from_beginning=*/false);

  if (span.first + start_offset < span.second - end_offset) {
    return {span.first + start_offset, span.second - end_offset};
  } else {
    return {span.first, span.first};
  }
}

float FeatureProcessor::SupportedCodepointsRatio(
    const TokenSpan& token_span, const std::vector<Token>& tokens) const {
  int num_supported = 0;
  int num_total = 0;
  for (int i = token_span.first; i < token_span.second; ++i) {
    const UnicodeText value =
        UTF8ToUnicodeText(tokens[i].value, /*do_copy=*/false);
    for (auto codepoint : value) {
      if (IsCodepointInRanges(codepoint, supported_codepoint_ranges_)) {
        ++num_supported;
      }
      ++num_total;
    }
  }
  // Avoid division by zero.
  if (num_total == 0) {
    return 0.0;
  }
  return static_cast<float>(num_supported) / static_cast<float>(num_total);
}

const std::string& FeatureProcessor::StripBoundaryCodepoints(
    const std::string& value, std::string* buffer) const {
  const UnicodeText value_unicode = UTF8ToUnicodeText(value, /*do_copy=*/false);
  const CodepointSpan initial_span{0, value_unicode.size_codepoints()};
  const CodepointSpan stripped_span =
      StripBoundaryCodepoints(value_unicode, initial_span);

  if (initial_span != stripped_span) {
    const UnicodeText stripped_token_value =
        UnicodeText::Substring(value_unicode, stripped_span.first,
                               stripped_span.second, /*do_copy=*/false);
    *buffer = stripped_token_value.ToUTF8String();
    return *buffer;
  }
  return value;
}

int FeatureProcessor::CollectionToLabel(const std::string& collection) const {
  const auto it = collection_to_label_.find(collection);
  if (it == collection_to_label_.end()) {
    return options_->default_collection();
  } else {
    return it->second;
  }
}

std::string FeatureProcessor::LabelToCollection(int label) const {
  if (label >= 0 && label < collection_to_label_.size()) {
    return (*options_->collections())[label]->str();
  } else {
    return GetDefaultCollection();
  }
}

void FeatureProcessor::MakeLabelMaps() {
  if (options_->collections() != nullptr) {
    for (int i = 0; i < options_->collections()->size(); ++i) {
      collection_to_label_[(*options_->collections())[i]->str()] = i;
    }
  }

  int selection_label_id = 0;
  for (int l = 0; l < (options_->max_selection_span() + 1); ++l) {
    for (int r = 0; r < (options_->max_selection_span() + 1); ++r) {
      if (!options_->selection_reduced_output_space() ||
          r + l <= options_->max_selection_span()) {
        TokenSpan token_span{l, r};
        selection_to_label_[token_span] = selection_label_id;
        label_to_selection_.push_back(token_span);
        ++selection_label_id;
      }
    }
  }
}

void FeatureProcessor::RetokenizeAndFindClick(const std::string& context,
                                              const CodepointSpan& input_span,
                                              bool only_use_line_with_click,
                                              std::vector<Token>* tokens,
                                              int* click_pos) const {
  const UnicodeText context_unicode =
      UTF8ToUnicodeText(context, /*do_copy=*/false);
  const auto [span_begin, span_end] =
      CodepointSpanToUnicodeTextRange(context_unicode, input_span);
  RetokenizeAndFindClick(context_unicode, span_begin, span_end, input_span,
                         only_use_line_with_click, tokens, click_pos);
}

void FeatureProcessor::RetokenizeAndFindClick(
    const UnicodeText& context_unicode,
    const UnicodeText::const_iterator& span_begin,
    const UnicodeText::const_iterator& span_end,
    const CodepointSpan& input_span, bool only_use_line_with_click,
    std::vector<Token>* tokens, int* click_pos) const {
  TC3_CHECK(tokens != nullptr);

  if (options_->split_tokens_on_selection_boundaries()) {
    internal::SplitTokensOnSelectionBoundaries(input_span, tokens);
  }

  if (only_use_line_with_click) {
    StripTokensFromOtherLines(context_unicode, span_begin, span_end, input_span,
                              tokens);
  }

  int local_click_pos;
  if (click_pos == nullptr) {
    click_pos = &local_click_pos;
  }
  *click_pos = FindCenterToken(input_span, *tokens);
  if (*click_pos == kInvalidIndex) {
    // If the default click method failed, let's try to do sub-token matching
    // before we fail.
    *click_pos = internal::CenterTokenFromClick(input_span, *tokens);
  }
}

namespace internal {

void StripOrPadTokens(const TokenSpan& relative_click_span, int context_size,
                      std::vector<Token>* tokens, int* click_pos) {
  int right_context_needed = relative_click_span.second + context_size;
  if (*click_pos + right_context_needed + 1 >= tokens->size()) {
    // Pad max the context size.
    const int num_pad_tokens = std::min(
        context_size, static_cast<int>(*click_pos + right_context_needed + 1 -
                                       tokens->size()));
    std::vector<Token> pad_tokens(num_pad_tokens);
    tokens->insert(tokens->end(), pad_tokens.begin(), pad_tokens.end());
  } else if (*click_pos + right_context_needed + 1 < tokens->size() - 1) {
    // Strip unused tokens.
    auto it = tokens->begin();
    std::advance(it, *click_pos + right_context_needed + 1);
    tokens->erase(it, tokens->end());
  }

  int left_context_needed = relative_click_span.first + context_size;
  if (*click_pos < left_context_needed) {
    // Pad max the context size.
    const int num_pad_tokens =
        std::min(context_size, left_context_needed - *click_pos);
    std::vector<Token> pad_tokens(num_pad_tokens);
    tokens->insert(tokens->begin(), pad_tokens.begin(), pad_tokens.end());
    *click_pos += num_pad_tokens;
  } else if (*click_pos > left_context_needed) {
    // Strip unused tokens.
    auto it = tokens->begin();
    std::advance(it, *click_pos - left_context_needed);
    *click_pos -= it - tokens->begin();
    tokens->erase(tokens->begin(), it);
  }
}

}  // namespace internal

bool FeatureProcessor::HasEnoughSupportedCodepoints(
    const std::vector<Token>& tokens, const TokenSpan& token_span) const {
  if (options_->min_supported_codepoint_ratio() > 0) {
    const float supported_codepoint_ratio =
        SupportedCodepointsRatio(token_span, tokens);
    if (supported_codepoint_ratio < options_->min_supported_codepoint_ratio()) {
      TC3_VLOG(1) << "Not enough supported codepoints in the context: "
                  << supported_codepoint_ratio;
      return false;
    }
  }
  return true;
}

bool FeatureProcessor::ExtractFeatures(
    const std::vector<Token>& tokens, const TokenSpan& token_span,
    const CodepointSpan& selection_span_for_feature,
    const EmbeddingExecutor* embedding_executor,
    EmbeddingCache* embedding_cache, int feature_vector_size,
    std::unique_ptr<CachedFeatures>* cached_features) const {
  std::unique_ptr<std::vector<float>> features(new std::vector<float>());
  features->reserve(feature_vector_size * token_span.Size());
  for (int i = token_span.first; i < token_span.second; ++i) {
    if (!AppendTokenFeaturesWithCache(tokens[i], selection_span_for_feature,
                                      embedding_executor, embedding_cache,
                                      features.get())) {
      TC3_LOG(ERROR) << "Could not get token features.";
      return false;
    }
  }

  std::unique_ptr<std::vector<float>> padding_features(
      new std::vector<float>());
  padding_features->reserve(feature_vector_size);
  if (!AppendTokenFeaturesWithCache(Token(), selection_span_for_feature,
                                    embedding_executor, embedding_cache,
                                    padding_features.get())) {
    TC3_LOG(ERROR) << "Count not get padding token features.";
    return false;
  }

  *cached_features = CachedFeatures::Create(token_span, std::move(features),
                                            std::move(padding_features),
                                            options_, feature_vector_size);
  if (!*cached_features) {
    TC3_LOG(ERROR) << "Cound not create cached features.";
    return false;
  }

  return true;
}

bool FeatureProcessor::AppendTokenFeaturesWithCache(
    const Token& token, const CodepointSpan& selection_span_for_feature,
    const EmbeddingExecutor* embedding_executor,
    EmbeddingCache* embedding_cache,
    std::vector<float>* output_features) const {
  // Look for the embedded features for the token in the cache, if there is one.
  if (embedding_cache) {
    const auto it = embedding_cache->find({token.start, token.end});
    if (it != embedding_cache->end()) {
      // The embedded features were found in the cache, extract only the dense
      // features.
      std::vector<float> dense_features;
      if (!feature_extractor_.Extract(
              token, token.IsContainedInSpan(selection_span_for_feature),
              /*sparse_features=*/nullptr, &dense_features)) {
        TC3_LOG(ERROR) << "Could not extract token's dense features.";
        return false;
      }

      // Append both embedded and dense features to the output and return.
      output_features->insert(output_features->end(), it->second.begin(),
                              it->second.end());
      output_features->insert(output_features->end(), dense_features.begin(),
                              dense_features.end());
      return true;
    }
  }

  // Extract the sparse and dense features.
  std::vector<int> sparse_features;
  std::vector<float> dense_features;
  if (!feature_extractor_.Extract(
          token, token.IsContainedInSpan(selection_span_for_feature),
          &sparse_features, &dense_features)) {
    TC3_LOG(ERROR) << "Could not extract token's features.";
    return false;
  }

  // Embed the sparse features, appending them directly to the output.
  const int embedding_size = GetOptions()->embedding_size();
  output_features->resize(output_features->size() + embedding_size);
  float* output_features_end =
      output_features->data() + output_features->size();
  if (!embedding_executor->AddEmbedding(
          TensorView<int>(sparse_features.data(),
                          {static_cast<int>(sparse_features.size())}),
          /*dest=*/output_features_end - embedding_size,
          /*dest_size=*/embedding_size)) {
    TC3_LOG(ERROR) << "Cound not embed token's sparse features.";
    return false;
  }

  // If there is a cache, the embedded features for the token were not in it,
  // so insert them.
  if (embedding_cache) {
    (*embedding_cache)[{token.start, token.end}] = std::vector<float>(
        output_features_end - embedding_size, output_features_end);
  }

  // Append the dense features to the output.
  output_features->insert(output_features->end(), dense_features.begin(),
                          dense_features.end());
  return true;
}

}  // namespace libtextclassifier3

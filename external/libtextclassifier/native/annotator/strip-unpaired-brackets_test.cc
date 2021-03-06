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

#include "annotator/strip-unpaired-brackets.h"

#include "gtest/gtest.h"

namespace libtextclassifier3 {
namespace {

class StripUnpairedBracketsTest : public ::testing::Test {
 protected:
  StripUnpairedBracketsTest() : INIT_UNILIB_FOR_TESTING(unilib_) {}
  UniLib unilib_;
};

TEST_F(StripUnpairedBracketsTest, StripUnpairedBrackets) {
  // If the brackets match, nothing gets stripped.
  EXPECT_EQ(StripUnpairedBrackets("call me (123) 456 today", {8, 17}, unilib_),
            CodepointSpan(8, 17));
  EXPECT_EQ(StripUnpairedBrackets("call me (123 456) today", {8, 17}, unilib_),
            CodepointSpan(8, 17));

  // If the brackets don't match, they get stripped.
  EXPECT_EQ(StripUnpairedBrackets("call me (123 456 today", {8, 16}, unilib_),
            CodepointSpan(9, 16));
  EXPECT_EQ(StripUnpairedBrackets("call me )123 456 today", {8, 16}, unilib_),
            CodepointSpan(9, 16));
  EXPECT_EQ(StripUnpairedBrackets("call me 123 456) today", {8, 16}, unilib_),
            CodepointSpan(8, 15));
  EXPECT_EQ(StripUnpairedBrackets("call me 123 456( today", {8, 16}, unilib_),
            CodepointSpan(8, 15));

  // Strips brackets correctly from length-1 selections that consist of
  // a bracket only.
  EXPECT_EQ(StripUnpairedBrackets("call me at ) today", {11, 12}, unilib_),
            CodepointSpan(12, 12));
  EXPECT_EQ(StripUnpairedBrackets("call me at ( today", {11, 12}, unilib_),
            CodepointSpan(12, 12));

  // Handles invalid spans gracefully.
  EXPECT_EQ(StripUnpairedBrackets("call me at  today", {11, 11}, unilib_),
            CodepointSpan(11, 11));
  EXPECT_EQ(StripUnpairedBrackets("hello world", {0, 0}, unilib_),
            CodepointSpan(0, 0));
  EXPECT_EQ(StripUnpairedBrackets("hello world", {11, 11}, unilib_),
            CodepointSpan(11, 11));
  EXPECT_EQ(StripUnpairedBrackets("hello world", {-1, -1}, unilib_),
            CodepointSpan(-1, -1));
}

}  // namespace
}  // namespace libtextclassifier3

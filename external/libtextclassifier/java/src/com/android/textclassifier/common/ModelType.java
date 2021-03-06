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

package com.android.textclassifier.common;

import androidx.annotation.StringDef;
import com.google.common.collect.ImmutableList;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

/** Effectively an enum class to represent types of models. */
public final class ModelType {
  /** TextClassifier model types as String. */
  @Retention(RetentionPolicy.SOURCE)
  @StringDef({ANNOTATOR, LANG_ID, ACTIONS_SUGGESTIONS})
  public @interface ModelTypeDef {}

  public static final String ANNOTATOR = "annotator";
  public static final String LANG_ID = "lang_id";
  public static final String ACTIONS_SUGGESTIONS = "actions_suggestions";

  public static final ImmutableList<String> VALUES =
      ImmutableList.of(ANNOTATOR, LANG_ID, ACTIONS_SUGGESTIONS);

  public static ImmutableList<String> values() {
    return VALUES;
  }

  private ModelType() {}
}

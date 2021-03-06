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
package android.inputmethodservice.cts.common;

/**
 * Constant table for test EditText app.
 */
public class EditTextAppConstants {
    // This is constants holding class, can't instantiate.
    private EditTextAppConstants() {}

    public static final String PACKAGE = "android.inputmethodservice.cts.edittextapp";
    public static final String CLASS =   PACKAGE + ".MainActivity";
    public static final String APK = "EditTextApp.apk";
    public static final String EDIT_TEXT_RES_NAME = PACKAGE + ":id/edit_text_entry";
    public static final String URI =
            "https://example.com/android/inputmethodservice/cts/edittextapp";
}

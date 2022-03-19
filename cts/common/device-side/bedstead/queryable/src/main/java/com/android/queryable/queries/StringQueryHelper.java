/*
 * Copyright (C) 2021 The Android Open Source Project
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

package com.android.queryable.queries;

import com.android.queryable.Queryable;

import java.io.Serializable;

/** Implementation of {@link StringQuery}. */
public final class StringQueryHelper<E extends Queryable>
        implements StringQuery<E>, Serializable{

    private final E mQuery;
    private String mEqualsValue = null;

    StringQueryHelper() {
        mQuery = (E) this;
    }

    public StringQueryHelper(E query) {
        mQuery = query;
    }

    @Override
    public E isEqualTo(String string) {
        this.mEqualsValue = string;
        return mQuery;
    }

    @Override
    public boolean matches(String value) {
        if (mEqualsValue != null && !mEqualsValue.equals(value)) {
            return false;
        }

        return true;
    }

    public static boolean matches(StringQueryHelper<?> stringQueryHelper, String value) {
        return stringQueryHelper.matches(value);
    }
}

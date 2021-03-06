/*
 * Copyright (C) 2017 The Android Open Source Project
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

package android.inputmethodservice.cts.db;

import android.database.Cursor;
import android.provider.BaseColumns;

import androidx.annotation.NonNull;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Abstraction of SQLite database row.
 * @param <E> type of entities.
 */
public final class Entity<E> {

    private final List<Field> mFields;
    private final Map<String, Field> mFieldMap;

    private Entity(Builder<E> builder) {
        mFields = builder.mFields;
        mFieldMap = builder.mFieldMap;
    }

    /**
     * Returns SQL statement to create this entity/row, such that
     * "(_id INTEGER PRIMARY KEY AUTOINCREMENT, column2_name column2_type, ...)".
     */
    String createEntitySql() {
        final StringBuilder sb = new StringBuilder("(");
        for (Field field : mFields) {
            if (field.mPos > 0) sb.append(", ");
            sb.append(field.mName).append(" ").append(field.mSqLiteType);
            if (field.mName.equals(BaseColumns._ID)) {
                sb.append(" PRIMARY KEY AUTOINCREMENT");
            }
        }
        return sb.append(")").toString();
    }

    Field getField(String fieldName) {
        return mFieldMap.get(fieldName);
    }

    /**
     * {@link Entity} builder.
     * @param <E> type of entities.
     */
    public static final class Builder<E> {
        private final List<Field> mFields = new ArrayList<>();
        private final Map<String, Field> mFieldMap = new HashMap<>();
        private int mPos = 0;

        /**
         * Constructor or {@link Builder}.
         */
        public Builder() {
            addFieldInternal(BaseColumns._ID, Cursor.FIELD_TYPE_INTEGER);
        }

        /**
         * Add a new field with given name and type.
         *
         * @param name name of the field
         * @param fieldType type enum of the field
         * @return this builder, useful for chaining
         */
        public Builder<E> addField(@NonNull String name, int fieldType) {
            addFieldInternal(name, fieldType);
            return this;
        }

        /**
         * Build {@link Entity}.
         *
         * @return a new instance of {@link Entity} built from this builder.
         */
        public Entity<E> build() {
            return new Entity<>(this);
        }

        private void addFieldInternal(String name, int fieldType) {
            if (mFieldMap.containsKey(name)) {
                throw new IllegalArgumentException("Field " + name + " already exists at "
                        + mFieldMap.get(name).mPos);
            }
            final Field field = Field.newInstance(mPos++, name, fieldType);
            mFields.add(field);
            mFieldMap.put(field.mName, field);
        }
    }
}

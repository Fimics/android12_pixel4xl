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

package com.android.compatibility.common.util;

import androidx.annotation.NonNull;

import org.junit.rules.TestRule;
import org.junit.runner.Description;
import org.junit.runners.model.Statement;

import java.util.Objects;

/**
 * JUnit rule used to restore a state after the test is run.
 *
 * <p>It stores the current state before the test, and restores it after the test (if necessary).
 *
 * @param <T> value type
 */
public class StateKeeperRule<T> implements TestRule {

    private final StateManager<T> mStateManager;

    /**
     * Default constructor.
     *
     * @param stateManager abstraction used to mange the state.
     */
    public StateKeeperRule(@NonNull StateManager<T> stateManager) {
        mStateManager = Objects.requireNonNull(stateManager);
    }

    /**
     * Hook for subclasses.
     */
    protected void preEvaluate(@SuppressWarnings("unused") Description description) {
    }

    /**
     * Hook for subclasses.
     */
    protected void postEvaluate(@SuppressWarnings("unused") Description description) {
    }

    @Override
    public Statement apply(Statement base, Description description) {
        return new Statement() {

            @Override
            public void evaluate() throws Throwable {
                final T previousValue = mStateManager.get();
                preEvaluate(description);
                try {
                    base.evaluate();
                } finally {
                    final T currentValue = mStateManager.get();
                    if (!Objects.equals(previousValue, currentValue)) {
                        mStateManager.set(previousValue);
                    }
                }
                postEvaluate(description);
            }
        };
    }
}

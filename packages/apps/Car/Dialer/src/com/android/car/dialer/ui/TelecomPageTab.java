/*
 * Copyright (C) 2019 The Android Open Source Project
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

package com.android.car.dialer.ui;

import android.content.Context;
import android.graphics.drawable.Drawable;

import androidx.annotation.Nullable;
import androidx.annotation.StringDef;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;

import com.android.car.dialer.R;
import com.android.car.dialer.ui.calllog.CallHistoryFragment;
import com.android.car.dialer.ui.common.OnItemClickedListener;
import com.android.car.dialer.ui.contact.ContactListFragment;
import com.android.car.dialer.ui.dialpad.DialpadFragment;
import com.android.car.dialer.ui.favorite.FavoriteFragment;
import com.android.car.ui.toolbar.Tab;

import com.google.common.collect.ImmutableMap;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Tab presenting fragments.
 */
public class TelecomPageTab {

    /**
     * Note: the strings must be consist with the items in string array tabs_config
     */
    @StringDef({
            TelecomPageTab.Page.FAVORITES,
            TelecomPageTab.Page.CALL_HISTORY,
            TelecomPageTab.Page.CONTACTS,
            TelecomPageTab.Page.DIAL_PAD
    })
    public @interface Page {
        String FAVORITES = "FAVORITE";
        String CALL_HISTORY = "CALL_HISTORY";
        String CONTACTS = "CONTACTS";
        String DIAL_PAD = "DIAL_PAD";
    }

    private final Factory mFactory;
    private Fragment mFragment;
    private String mFragmentTag;
    private boolean mWasFragmentRestored;
    private final Tab mToolbarTab;

    private TelecomPageTab(@Nullable Drawable icon, @Nullable String text,
            @Nullable OnItemClickedListener<TelecomPageTab> listener, Factory factory) {
        mFactory = factory;
        mToolbarTab = Tab.builder()
                .setIcon(icon)
                .setText(text)
                .setSelectedListener(listener == null
                        ? null
                        : tab -> listener.onItemClicked(this))
                .build();
    }

    public Tab getToolbarTab() {
        return mToolbarTab;
    }

    /**
     * Either restore fragment from saved state or create new instance.
     */
    private void initFragment(FragmentManager fragmentManager, @Page String page,
            boolean shouldForceRecreateFragment) {
        mFragmentTag = makeFragmentTag(page);
        mFragment = fragmentManager.findFragmentByTag(mFragmentTag);
        if (mFragment == null || shouldForceRecreateFragment) {
            mFragment = mFactory.createFragment(page);
            mWasFragmentRestored = false;
            return;
        }
        mWasFragmentRestored = true;
    }

    /**
     * Returns true if the fragment for this tab is restored from a saved state.
     */
    public boolean wasFragmentRestored() {
        return mWasFragmentRestored;
    }

    /**
     * Returns the fragment for this tab.
     */
    public Fragment getFragment() {
        return mFragment;
    }

    /**
     * Returns the fragment tag for this tab.
     */
    public String getFragmentTag() {
        return mFragmentTag;
    }

    private String makeFragmentTag(@Page String page) {
        return String.format("%s:%s", getClass().getSimpleName(), page);
    }

    /**
     * Responsible for creating the top tab items and their fragments.
     */
    public static class Factory {

        private static final ImmutableMap<String, Integer> TAB_LABELS =
                ImmutableMap.<String, Integer>builder()
                        .put(Page.FAVORITES, R.string.favorites_title)
                        .put(Page.CALL_HISTORY, R.string.call_history_title)
                        .put(Page.CONTACTS, R.string.contacts_title)
                        .put(Page.DIAL_PAD, R.string.dialpad_title)
                        .build();

        private static final ImmutableMap<String, Integer> TAB_ICONS =
                ImmutableMap.<String, Integer>builder()
                        .put(Page.FAVORITES, R.drawable.ic_favorite)
                        .put(Page.CALL_HISTORY, R.drawable.ic_history)
                        .put(Page.CONTACTS, R.drawable.ic_contact)
                        .put(Page.DIAL_PAD, R.drawable.ic_dialpad)
                        .build();

        private final FragmentManager mFragmentManager;
        private final Map<String, Integer> mTabPageIndexMap;
        private final String[] mTabConfig;
        private final List<TelecomPageTab> mTabs = new ArrayList<>();
        private final OnItemClickedListener<TelecomPageTab> mSelectedListener;

        public Factory(Context context,
                OnItemClickedListener<TelecomPageTab> listener,
                FragmentManager fragmentManager) {
            mFragmentManager = fragmentManager;
            mSelectedListener = listener;

            mTabConfig = context.getResources().getStringArray(R.array.tabs_config);

            mTabPageIndexMap = new HashMap<>();
            for (int i = 0; i < getTabCount(); i++) {
                mTabPageIndexMap.put(mTabConfig[i], i);
            }
        }

        private Fragment createFragment(@Page String page) {
            switch (page) {
                case Page.FAVORITES:
                    return FavoriteFragment.newInstance();
                case Page.CALL_HISTORY:
                    return CallHistoryFragment.newInstance();
                case Page.CONTACTS:
                    return ContactListFragment.newInstance();
                case Page.DIAL_PAD:
                    return DialpadFragment.newPlaceCallDialpad();
                default:
                    throw new UnsupportedOperationException("Tab is not supported.");
            }
        }

        /**
         * Create the tab for the given {@param tabIndex}
         */
        public List<TelecomPageTab> recreateTabs(Context context, boolean forceInit) {
            mTabs.clear();
            for (int i = 0; i < getTabCount(); i++) {
                String page = mTabConfig[i];
                TelecomPageTab telecomPageTab = new TelecomPageTab(
                        context.getDrawable(TAB_ICONS.get(page)),
                        context.getString(TAB_LABELS.get(page)),
                        mSelectedListener,
                        this);
                telecomPageTab.initFragment(mFragmentManager, page, forceInit);
                mTabs.add(telecomPageTab);
            }
            return mTabs;
        }

        public int getTabCount() {
            return mTabConfig.length;
        }

        /**
         * Returns the index for the given {@param page}
         */
        public int getTabIndex(@Page String page) {
            return mTabPageIndexMap.getOrDefault(page, -1);
        }

        /**
         * Returns the {@link TelecomPageTab} at the given index
         */
        public TelecomPageTab getTab(int index) {
            return mTabs.get(index);
        }
    }
}

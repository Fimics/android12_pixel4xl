/**
 * Copyright (c) 2020, The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef CPP_WATCHDOG_SERVER_SRC_UIDIOSTATS_H_
#define CPP_WATCHDOG_SERVER_SRC_UIDIOSTATS_H_

#include <android-base/result.h>
#include <android-base/stringprintf.h>
#include <utils/Mutex.h>
#include <utils/RefBase.h>

#include <stdint.h>

#include <string>
#include <unordered_map>

namespace android {
namespace automotive {
namespace watchdog {

constexpr const char* kUidIoStatsPath = "/proc/uid_io/stats";

enum UidState {
    FOREGROUND = 0,
    BACKGROUND,
    UID_STATES,
};

enum MetricType {
    READ_BYTES = 0,  // bytes read (from storage layer)
    WRITE_BYTES,     // bytes written (to storage layer)
    FSYNC_COUNT,     // number of fsync syscalls
    METRIC_TYPES,
};

class IoUsage {
public:
    IoUsage() : metrics{{0}} {};
    IoUsage(int64_t fgRdBytes, int64_t bgRdBytes, int64_t fgWrBytes, int64_t bgWrBytes,
            int64_t fgFsync, int64_t bgFsync) {
        metrics[READ_BYTES][FOREGROUND] = fgRdBytes;
        metrics[READ_BYTES][BACKGROUND] = bgRdBytes;
        metrics[WRITE_BYTES][FOREGROUND] = fgWrBytes;
        metrics[WRITE_BYTES][BACKGROUND] = bgWrBytes;
        metrics[FSYNC_COUNT][FOREGROUND] = fgFsync;
        metrics[FSYNC_COUNT][BACKGROUND] = bgFsync;
    }
    IoUsage& operator-=(const IoUsage& rhs);
    bool operator==(const IoUsage& usage) const {
        return memcmp(&metrics, &usage.metrics, sizeof(metrics)) == 0;
    }
    int64_t sumReadBytes() const {
        const auto& [fgBytes, bgBytes] =
                std::tuple(metrics[READ_BYTES][FOREGROUND], metrics[READ_BYTES][BACKGROUND]);
        return (std::numeric_limits<int64_t>::max() - fgBytes) > bgBytes
                ? (fgBytes + bgBytes)
                : std::numeric_limits<int64_t>::max();
    }
    int64_t sumWriteBytes() const {
        const auto& [fgBytes, bgBytes] =
                std::tuple(metrics[WRITE_BYTES][FOREGROUND], metrics[WRITE_BYTES][BACKGROUND]);
        return (std::numeric_limits<int64_t>::max() - fgBytes) > bgBytes
                ? (fgBytes + bgBytes)
                : std::numeric_limits<int64_t>::max();
    }
    bool isZero() const;
    std::string toString() const;
    int64_t metrics[METRIC_TYPES][UID_STATES];
};

struct UidIoUsage {
    uid_t uid = 0;  // Linux user id.
    IoUsage ios = {};
    UidIoUsage& operator-=(const UidIoUsage& rhs) {
        ios -= rhs.ios;
        return *this;
    }
    bool operator==(const UidIoUsage& rhs) const { return uid == rhs.uid && ios == rhs.ios; }
    std::string toString() const {
        return android::base::StringPrintf("Uid: %d, Usage: {%s}", uid, ios.toString().c_str());
    }
};

class UidIoStats : public RefBase {
public:
    explicit UidIoStats(const std::string& path = kUidIoStatsPath) :
          kEnabled(!access(path.c_str(), R_OK)), kPath(path) {}

    virtual ~UidIoStats() {}

    // Collects the per-UID I/O usage.
    virtual android::base::Result<void> collect();

    virtual const std::unordered_map<uid_t, UidIoUsage> latestStats() const {
        Mutex::Autolock lock(mMutex);
        return mLatestUidIoUsages;
    }

    virtual const std::unordered_map<uid_t, UidIoUsage> deltaStats() const {
        Mutex::Autolock lock(mMutex);
        return mDeltaUidIoUsages;
    }

    // Returns true when the uid_io stats file is accessible. Otherwise, returns false.
    // Called by IoPerfCollection and tests.
    virtual bool enabled() { return kEnabled; }

    virtual std::string filePath() { return kPath; }

private:
    // Reads the contents of |kPath|.
    android::base::Result<std::unordered_map<uid_t, UidIoUsage>> getUidIoUsagesLocked() const;

    // Makes sure only one collection is running at any given time.
    mutable Mutex mMutex;

    // Latest dump from the file at |kPath|.
    std::unordered_map<uid_t, UidIoUsage> mLatestUidIoUsages GUARDED_BY(mMutex);

    // Delta of per-UID I/O usage since last before collection.
    std::unordered_map<uid_t, UidIoUsage> mDeltaUidIoUsages GUARDED_BY(mMutex);

    // True if kPath is accessible.
    const bool kEnabled;

    // Path to uid_io stats file. Default path is |kUidIoStatsPath|.
    const std::string kPath;
};

}  // namespace watchdog
}  // namespace automotive
}  // namespace android

#endif  //  CPP_WATCHDOG_SERVER_SRC_UIDIOSTATS_H_

// Copyright 2020 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef ANDROID_V4L2_CODEC2_COMMON_HELPERS_H
#define ANDROID_V4L2_CODEC2_COMMON_HELPERS_H

#include <C2Config.h>
#include <system/graphics.h>
#include <ui/Size.h>

#include <v4l2_codec2/common/VideoPixelFormat.h>

namespace android {

// The encoder parameter set.
//  |mInputFormat| is the pixel format of the input frames.
//  |mInputVisibleSize| is the resolution of the input frames.
//  |mOutputProfile| is the codec profile of the encoded output stream.
//  |mInitialBitrate| is the initial bitrate of the encoded output stream, in bits per second.
//  |mInitialFramerate| is the initial requested framerate.
//  |mH264OutputLevel| is H264 level of encoded output stream.
//  |mStorageType| is the storage type of video frame provided on encode().
struct VideoEncoderAcceleratorConfig {
    enum VideoFrameStorageType {
        SHMEM = 0,
        DMABUF = 1,
    };

    VideoPixelFormat mInputFormat;
    ui::Size mInputVisibleSize;
    C2Config::profile_t mOutputProfile;
    uint32_t mInitialBitrate;
    uint32_t mInitialFramerate;
    uint8_t mH264OutputLevel;
    VideoFrameStorageType mStorageType;
};

// Convert the specified C2Config level to a V4L2 level.
uint8_t c2LevelToV4L2Level(C2Config::level_t level);

// Get the specified graphics block in YCbCr format.
android_ycbcr getGraphicBlockInfo(const C2ConstGraphicBlock& block);

// When encoding a video the codec-specific data (CSD; e.g. SPS and PPS for H264 encoding) will be
// concatenated to the first encoded slice. This function extracts the CSD out of the bitstream and
// stores it into |csd|.
void extractCSDInfo(std::unique_ptr<C2StreamInitDataInfo::output>* const csd, const uint8_t* data,
                    size_t length);

}  // namespace android

#endif  // ANDROID_V4L2_CODEC2_COMMON_HELPERS_H

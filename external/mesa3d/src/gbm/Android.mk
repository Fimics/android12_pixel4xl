#
# Copyright (C) 2016 Linaro, Ltd., Rob Herring <robh@kernel.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

LOCAL_PATH := $(call my-dir)

include $(LOCAL_PATH)/Makefile.sources

include $(CLEAR_VARS)

LOCAL_EXPORT_C_INCLUDE_DIRS := \
	$(LOCAL_PATH)/main

LOCAL_C_INCLUDES := \
	$(LOCAL_PATH)/main

LOCAL_STATIC_LIBRARIES := \
	libmesa_util \
	libmesa_loader

LOCAL_MODULE := libgbm_mesa
LOCAL_LICENSE_KINDS := SPDX-license-identifier-MIT
LOCAL_LICENSE_CONDITIONS := notice
LOCAL_NOTICE_FILE := $(LOCAL_PATH)/../../LICENSE

LOCAL_SRC_FILES := \
	$(gbm_core_FILES) \
	$(gbm_dri_FILES)

include $(MESA_COMMON_MK)
include $(BUILD_SHARED_LIBRARY)

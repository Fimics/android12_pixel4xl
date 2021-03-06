ifneq ($(BOARD_VENDOR_QCOM_GPS_LOC_API_HARDWARE),)
ifneq ($(BUILD_TINY_ANDROID),true)
#Compile this library only for builds with the latest modem image

LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

## Libs
LOCAL_SHARED_LIBRARIES := \
    libutils \
    libcutils \
    liblog \
    libloc_stub \
    libprocessgroup

LOCAL_SRC_FILES += \
        platform_lib_gettid.cpp \
        platform_lib_log_util.cpp \
        platform_lib_property_service.cpp \
        platform_lib_sched_policy.cpp \
        platform_lib_time.cpp

LOCAL_CFLAGS += \
     -fno-short-enums \
     -D_ANDROID_ \
     -std=c++11

## Includes
LOCAL_C_INCLUDES:= \
    $(LOCAL_PATH)/../include \
    $(TARGET_OUT_HEADERS)/gps.utils \
    $(TARGET_OUT_HEADERS)/libloc_stub

LOCAL_COPY_HEADERS_TO:= libloc_pla/
LOCAL_COPY_HEADERS:= \
        ../include/platform_lib_gettid.h \
        ../include/platform_lib_includes.h \
        ../include/platform_lib_log_util.h \
        ../include/platform_lib_macros.h \
        ../include/platform_lib_property_service.h \
        ../include/platform_lib_sched_policy.h \
        ../include/platform_lib_time.h

LOCAL_MODULE := libloc_pla
LOCAL_LICENSE_KINDS := SPDX-license-identifier-BSD
LOCAL_LICENSE_CONDITIONS := notice
LOCAL_VENDOR_MODULE := true
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE_OWNER := qti

LOCAL_PRELINK_MODULE := false

include $(BUILD_SHARED_LIBRARY)
endif # not BUILD_TINY_ANDROID
endif # BOARD_VENDOR_QCOM_GPS_LOC_API_HARDWARE

/*
 * Copyright (C) 2015 The Android Open Source Project
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

/* This file is used to define the properties of the filesystem
** images generated by build tools (mkbootfs and mkyaffs2image) and
** by the device side of adb.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#include <selinux/label.h>
#include <selinux/selinux.h>

#include "android.h"
#include "private/android_filesystem_config.h"
#include "private/canned_fs_config.h"
#include "private/fs_config.h"

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

void alloc_mounted_path(const char *mount_point, const char *subpath, char **mounted_path) {
    *mounted_path = malloc(strlen(mount_point) + strlen(subpath) + 1);
    if (*mounted_path == NULL) {
        perror("Malloc Failure.");
        exit(EXIT_FAILURE);
    }
    strcpy(*mounted_path, mount_point);
    strcat(*mounted_path, subpath);
}

void android_fs_config(fs_config_func_t fs_config_func, const char *path, struct stat *stat,
        const char *target_out_path, uint64_t *capabilities) {
    // filesystem_config does not preserve file type bits
    mode_t stat_file_type_mask = stat->st_mode & S_IFMT;
    unsigned int uid = 0, gid = 0, mode = 0;
    if (fs_config_func) {
        fs_config_func(path, S_ISDIR(stat->st_mode), target_out_path,
                  &uid, &gid, &mode, capabilities);
        stat->st_uid = uid;
        stat->st_gid = gid;
        stat->st_mode = mode;
    }
    stat->st_mode |= stat_file_type_mask;
}


struct selabel_handle *get_sehnd(const char *context_file) {
    struct selinux_opt seopts[] = {
        {
            .type = SELABEL_OPT_PATH,
            .value = context_file
        }
    };
    struct selabel_handle *sehnd =
        selabel_open(SELABEL_CTX_FILE, seopts, ARRAY_SIZE(seopts));

    if (!sehnd) {
        perror("Error running selabel_open.");
        exit(EXIT_FAILURE);
    }
    return sehnd;
}


char *set_selabel(const char *path, unsigned int mode, struct selabel_handle *sehnd) {
    char *secontext;
    if (sehnd != NULL) {
        int full_name_size = strlen(path) + 2;
        char* full_name = (char*) malloc(full_name_size);
        if (full_name == NULL) {
            perror("Malloc Failure.");
            exit(EXIT_FAILURE);
        }

        full_name[0] = '/';
        strncpy(full_name + 1, path, full_name_size - 1);

        if (selabel_lookup(sehnd, &secontext, full_name, mode)) {
            secontext = strdup("u:object_r:unlabeled:s0");
        }

        free(full_name);
        return secontext;
    }
    perror("Selabel handle is NULL.");
    exit(EXIT_FAILURE);
}

struct vfs_cap_data set_caps(uint64_t capabilities) {
    struct vfs_cap_data cap_data;
    memset(&cap_data, 0, sizeof(cap_data));

    if (capabilities == 0)
        return cap_data;

    cap_data.magic_etc = VFS_CAP_REVISION_2 | VFS_CAP_FLAGS_EFFECTIVE;
    cap_data.data[0].permitted = (uint32_t) capabilities;
    cap_data.data[0].inheritable = 0;
    cap_data.data[1].permitted = (uint32_t) (capabilities >> 32);
    cap_data.data[1].inheritable = 0;

    return cap_data;
}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Generate a virtual cmd script for pass level bisection.

This is a required argument for pass level bisecting. For unit test, we use
this script to verify if cmd_script.sh is generated correctly.
"""

from __future__ import print_function

import os
import sys


def Main():
  if not os.path.exists('./is_setup'):
    return 1
  file_name = 'cmd_script.sh'
  with open(file_name, 'w', encoding='utf-8') as f:
    f.write('Generated by generate_cmd.py')
  return 0


if __name__ == '__main__':
  retval = Main()
  sys.exit(retval)

# Copyright (C) 2008 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.source "T_iput_short_15.java"
.class  public Ldot/junit/opcodes/iput_short/d/T_iput_short_15;
.super  Ldot/junit/opcodes/iput_short/d/T_iput_short_1;

.method public constructor <init>()V
.registers 1

       invoke-direct {v0}, Ldot/junit/opcodes/iput_short/d/T_iput_short_1;-><init>()V
       return-void
.end method

.method public run()V
.registers 3

       const/16 v1, 1
       iput-short v1, v2, Ldot/junit/opcodes/iput_short/d/T_iput_short_1;->st_pvt1:S
       return-void
.end method



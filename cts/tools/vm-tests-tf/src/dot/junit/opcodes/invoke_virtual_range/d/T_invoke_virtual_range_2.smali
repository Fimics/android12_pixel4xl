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

.source "T_invoke_virtual_range_2.java"
.class  public Ldot/junit/opcodes/invoke_virtual_range/d/T_invoke_virtual_range_2;
.super  Ljava/lang/Object;


.method public constructor <init>()V
.registers 2

       invoke-direct {v1}, Ljava/lang/Object;-><init>()V
       return-void
.end method

.method public test(IIIIIIIIII)I
.registers 11
    const v0, 10
    if-ne v0, v10, :Label0
    const v0, 9
    if-ne v0, v9, :Label0
    const v0, 8
    if-ne v0, v8, :Label0
    const v0, 7
    if-ne v0, v7, :Label0
    const v0, 6
    if-ne v0, v6, :Label0
    const v0, 5
    if-ne v0, v5, :Label0
    const v0, 4
    if-ne v0, v4, :Label0
    const v0, 3
    if-ne v0, v3, :Label0
    const v0, 2
    if-ne v0, v2, :Label0
    const v0, 1
    if-ne v0, v1, :Label0

    const v0, 1
    return v0
:Label0
    const v0, 0
    return v0

.end method

.method public run()I
.registers 16
       move-object v0, v15
         const v1, 1
          const v2, 2
          const v3, 3
          const v4, 4
          const v5, 5
          const v6, 6
          const v7, 7
          const v8, 8
          const v9, 9
          const v10, 10

       invoke-virtual/range {v0..v10}, Ldot/junit/opcodes/invoke_virtual_range/d/T_invoke_virtual_range_2;->test(IIIIIIIIII)I
       move-result v0
       return v0
.end method



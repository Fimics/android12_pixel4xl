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

/**
 * Tests for optimizations of break-loops, i.e. loops that break
 * out of a while-true loop when the end condition is satisfied.
 * In particular, the tests focus on break-loops that can be
 * rewritten into regular countable loops (this may improve certain
 * loops generated by the Kotlin compiler for inclusive ranges).
 */
public class Main {

  /// CHECK-START: int Main.breakLoop(int[]) induction_var_analysis (before)
  /// CHECK-DAG: <<Par:l\d+>>  ParameterValue                     loop:none
  /// CHECK-DAG: <<Zero:i\d+>> IntConstant 0                      loop:none
  /// CHECK-DAG: <<One:i\d+>>  IntConstant 1                      loop:none
  /// CHECK-DAG: <<Nil:l\d+>>  NullCheck [<<Par>>]                loop:none
  /// CHECK-DAG: <<Phi:i\d+>>  Phi [<<Zero>>,<<AddI:i\d+>>]       loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>  BoundsCheck [<<Phi>>,{{i\d+}}]     loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               ArraySet [<<Nil>>,<<Bnd>>,<<One>>] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<NE:z\d+>>   NotEqual [{{i\d+}},<<Phi>>]        loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               If [<<NE>>]                        loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>      Add [<<Phi>>,<<One>>]              loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-START: int Main.breakLoop(int[]) induction_var_analysis (after)
  /// CHECK-DAG: <<Par:l\d+>>  ParameterValue                     loop:none
  /// CHECK-DAG: <<Zero:i\d+>> IntConstant 0                      loop:none
  /// CHECK-DAG: <<One:i\d+>>  IntConstant 1                      loop:none
  /// CHECK-DAG: <<Nil:l\d+>>  NullCheck [<<Par>>]                loop:none
  /// CHECK-DAG: <<Phi:i\d+>>  Phi [<<Zero>>,<<AddI:i\d+>>]       loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<LE:z\d+>>   LessThanOrEqual [<<Phi>>,{{i\d+}}] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               If [<<LE>>]                        loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>  BoundsCheck [<<Phi>>,{{i\d+}}]     loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               ArraySet [<<Nil>>,<<Bnd>>,<<One>>] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>      Add [<<Phi>>,<<One>>]              loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-START-ARM64: int Main.breakLoop(int[]) loop_optimization (after)
  /// CHECK-DAG: <<Par:l\d+>>  ParameterValue                          loop:none
  /// CHECK-DAG: <<One:i\d+>>  IntConstant 1                           loop:none
  /// CHECK-DAG: <<Nil:l\d+>>  NullCheck [<<Par>>]                     loop:none
  /// CHECK-IF:     hasIsaFeature("sve")
  //
  ///     CHECK-DAG: <<Rep:d\d+>>   VecReplicateScalar [<<One>>,{{j\d+}}]             loop:none
  ///     CHECK-DAG: <<LoopP:j\d+>> VecPredWhile                                      loop:<<Loop:B\d+>> outer_loop:none
  ///     CHECK-DAG:                VecStore [<<Nil>>,<<Phi:i\d+>>,<<Rep>>,<<LoopP>>] loop:<<Loop>>      outer_loop:none
  ///     CHECK-DAG:                Add [<<Phi>>,{{i\d+}}]                            loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-ELSE:
  //
  ///     CHECK-DAG: <<Four:i\d+>>  IntConstant 4                           loop:none
  ///     CHECK-DAG: <<Rep:d\d+>>   VecReplicateScalar [<<One>>]            loop:none
  ///     CHECK-DAG:                VecStore [<<Nil>>,<<Phi:i\d+>>,<<Rep>>] loop:<<Loop:B\d+>> outer_loop:none
  ///     CHECK-DAG:                Add [<<Phi>>,<<Four>>]                  loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-FI:
  static int breakLoop(int[] a) {
    int l = 0;
    int u = a.length - 1;
    int i = l;
    if (l <= u) {
      while (true) {
        a[i] = 1;
        if (i == u) break;
        i++;
      }
    }
    return i;
  }

  /// CHECK-START: int Main.breakLoopDown(int[]) induction_var_analysis (before)
  /// CHECK-DAG: <<Par:l\d+>>  ParameterValue                     loop:none
  /// CHECK-DAG: <<Zero:i\d+>> IntConstant 0                      loop:none
  /// CHECK-DAG: <<MOne:i\d+>> IntConstant -1                     loop:none
  /// CHECK-DAG: <<Two:i\d+>>  IntConstant 2                      loop:none
  /// CHECK-DAG: <<Nil:l\d+>>  NullCheck [<<Par>>]                loop:none
  /// CHECK-DAG: <<Phi:i\d+>>  Phi [{{i\d+}},<<AddI:i\d+>>]       loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>  BoundsCheck [<<Phi>>,{{i\d+}}]     loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               ArraySet [<<Nil>>,<<Bnd>>,<<Two>>] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<NE:z\d+>>   NotEqual [<<Phi>>,<<Zero>>]        loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               If [<<NE>>]                        loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>      Add [<<Phi>>,<<MOne>>]             loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-START: int Main.breakLoopDown(int[]) induction_var_analysis (after)
  /// CHECK-DAG: <<Par:l\d+>>  ParameterValue                        loop:none
  /// CHECK-DAG: <<Zero:i\d+>> IntConstant 0                         loop:none
  /// CHECK-DAG: <<MOne:i\d+>> IntConstant -1                        loop:none
  /// CHECK-DAG: <<Two:i\d+>>  IntConstant 2                         loop:none
  /// CHECK-DAG: <<Nil:l\d+>>  NullCheck [<<Par>>]                   loop:none
  /// CHECK-DAG: <<Phi:i\d+>>  Phi [{{i\d+}},<<AddI:i\d+>>]          loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<GE:z\d+>>   GreaterThanOrEqual [<<Phi>>,<<Zero>>] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               If [<<GE>>]                           loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>  BoundsCheck [<<Phi>>,{{i\d+}}]        loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               ArraySet [<<Nil>>,<<Bnd>>,<<Two>>]    loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>      Add [<<Phi>>,<<MOne>>]                loop:<<Loop>>      outer_loop:none
  static int breakLoopDown(int[] a) {
    int l = 0;
    int u = a.length - 1;
    int i = u;
    if (u >= l) {
      while (true) {
        a[i] = 2;
        if (i == l) break;
        i--;
      }
    }
    return i;
  }

  /// CHECK-START: int Main.breakLoopSafeConst(int[]) induction_var_analysis (before)
  /// CHECK-DAG: <<Par:l\d+>>   ParameterValue                       loop:none
  /// CHECK-DAG: <<One:i\d+>>   IntConstant 1                        loop:none
  /// CHECK-DAG: <<Three:i\d+>> IntConstant 3                        loop:none
  /// CHECK-DAG: <<L1:i\d+>>    IntConstant 2147483631               loop:none
  /// CHECK-DAG: <<L2:i\d+>>    IntConstant 2147483646               loop:none
  /// CHECK-DAG: <<Phi:i\d+>>   Phi [<<L1>>,<<AddI:i\d+>>]           loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<Sub:i\d+>>   Sub [<<Phi>>,<<L1>>]                 loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Nil:l\d+>>   NullCheck [<<Par>>]                  loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>   BoundsCheck [<<Sub>>,{{i\d+}}]       loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:                ArraySet [<<Nil>>,<<Bnd>>,<<Three>>] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<NE:z\d+>>    NotEqual [<<Phi>>,<<L2>>]            loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:                If [<<NE>>]                          loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>       Add [<<Phi>>,<<One>>]                loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-START: int Main.breakLoopSafeConst(int[]) induction_var_analysis (after)
  /// CHECK-DAG: <<Par:l\d+>>  ParameterValue                        loop:none
  /// CHECK-DAG: <<One:i\d+>>   IntConstant 1                        loop:none
  /// CHECK-DAG: <<Three:i\d+>> IntConstant 3                        loop:none
  /// CHECK-DAG: <<L1:i\d+>>    IntConstant 2147483631               loop:none
  /// CHECK-DAG: <<L2:i\d+>>    IntConstant 2147483646               loop:none
  /// CHECK-DAG: <<Phi:i\d+>>   Phi [<<L1>>,<<AddI:i\d+>>]           loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<LE:z\d+>>    LessThanOrEqual [<<Phi>>,<<L2>>]     loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Sub:i\d+>>   Sub [<<Phi>>,<<L1>>]                 loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Nil:l\d+>>   NullCheck [<<Par>>]                  loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>   BoundsCheck [<<Sub>>,{{i\d+}}]       loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:                ArraySet [<<Nil>>,<<Bnd>>,<<Three>>] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>       Add [<<Phi>>,<<One>>]                loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-START-ARM64: int Main.breakLoopSafeConst(int[]) loop_optimization (after)
  /// CHECK-DAG: <<Par:l\d+>>   ParameterValue                          loop:none
  /// CHECK-DAG: <<One:i\d+>>   IntConstant 1                           loop:none
  /// CHECK-DAG: <<Three:i\d+>> IntConstant 3                           loop:none
  /// CHECK-IF:     hasIsaFeature("sve")
  //
  ///     CHECK-DAG: <<Rep:d\d+>>   VecReplicateScalar [<<Three>>,{{j\d+}}]           loop:none
  ///     CHECK-DAG: <<LoopP:j\d+>> VecPredWhile                                      loop:<<Loop:B\d+>> outer_loop:none
  ///     CHECK-DAG:                VecStore [<<Par>>,<<Phi:i\d+>>,<<Rep>>,<<LoopP>>] loop:<<Loop>>      outer_loop:none
  ///     CHECK-DAG:                Add [<<Phi>>,{{i\d+}}]                            loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-ELSE:
  //
  ///     CHECK-DAG: <<Four:i\d+>>  IntConstant 4                           loop:none
  ///     CHECK-DAG: <<Rep:d\d+>>   VecReplicateScalar [<<Three>>]          loop:none
  ///     CHECK-DAG:                VecStore [<<Par>>,<<Phi:i\d+>>,<<Rep>>] loop:<<Loop:B\d+>> outer_loop:none
  ///     CHECK-DAG:                Add [<<Phi>>,<<Four>>]                  loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-FI:
  static int breakLoopSafeConst(int[] a) {
    int l = Integer.MAX_VALUE - 16;
    int u = Integer.MAX_VALUE - 1;
    int i = l;
    if (l <= u) {  // will be removed by simplifier
      while (true) {
        a[i - l] = 3;
        if (i == u) break;
        i++;
      }
    }
    return i;
  }

  /// CHECK-START: int Main.breakLoopUnsafeConst(int[]) induction_var_analysis (before)
  /// CHECK-DAG: <<Par:l\d+>>   ParameterValue                       loop:none
  /// CHECK-DAG: <<One:i\d+>>   IntConstant 1                        loop:none
  /// CHECK-DAG: <<Four:i\d+>>  IntConstant 4                        loop:none
  /// CHECK-DAG: <<L1:i\d+>>    IntConstant 2147483632               loop:none
  /// CHECK-DAG: <<L2:i\d+>>    IntConstant 2147483647               loop:none
  /// CHECK-DAG: <<Phi:i\d+>>   Phi [<<L1>>,<<AddI:i\d+>>]           loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<Sub:i\d+>>   Sub [<<Phi>>,<<L1>>]                 loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Nil:l\d+>>   NullCheck [<<Par>>]                  loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>   BoundsCheck [<<Sub>>,{{i\d+}}]       loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:                ArraySet [<<Nil>>,<<Bnd>>,<<Four>>]  loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<NE:z\d+>>    NotEqual [<<Phi>>,<<L2>>]            loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:                If [<<NE>>]                          loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>       Add [<<Phi>>,<<One>>]                loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-START: int Main.breakLoopUnsafeConst(int[]) induction_var_analysis (after)
  /// CHECK-DAG:                NotEqual
  /// CHECK-NOT:                LessThanOrEqual
  static int breakLoopUnsafeConst(int[] a) {
    int l = Integer.MAX_VALUE - 15;
    int u = Integer.MAX_VALUE;
    int i = l;
    if (l <= u) {  // will be removed by simplifier
      while (true) {
        a[i - l] = 4;
        if (i == u) break;  // rewriting exit not safe!
        i++;
      }
    }
    return i;
  }

  /// CHECK-START: int Main.breakLoopNastyPhi(int[]) induction_var_analysis (before)
  /// CHECK-DAG: <<Par:l\d+>>  ParameterValue                      loop:none
  /// CHECK-DAG: <<Zero:i\d+>> IntConstant 0                       loop:none
  /// CHECK-DAG: <<One:i\d+>>  IntConstant 1                       loop:none
  /// CHECK-DAG: <<Five:i\d+>> IntConstant 5                       loop:none
  /// CHECK-DAG: <<M123:i\d+>> IntConstant -123                    loop:none
  /// CHECK-DAG: <<Nil:l\d+>>  NullCheck [<<Par>>]                 loop:none
  /// CHECK-DAG: <<Phi:i\d+>>  Phi [<<Zero>>,<<AddI:i\d+>>]        loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<Wrap:i\d+>> Phi [<<M123>>,<<Phi>>]              loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>  BoundsCheck [<<Phi>>,{{i\d+}}]      loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               ArraySet [<<Nil>>,<<Bnd>>,<<Five>>] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<NE:z\d+>>   NotEqual [{{i\d+}},<<Phi>>]         loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               If [<<NE>>]                         loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>      Add [<<Phi>>,<<One>>]               loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Comb:i\d+>> Phi [<<M123>>,<<Wrap>>]             loop:none
  /// CHECK-DAG:               Return [<<Comb>>]                   loop:none
  //
  /// CHECK-START: int Main.breakLoopNastyPhi(int[]) induction_var_analysis (after)
  /// CHECK-DAG:               NotEqual
  /// CHECK-NOT:               LessThanOrEqual
  static int breakLoopNastyPhi(int[] a) {
    int l = 0;
    int u = a.length - 1;
    int x = -123;
    if (l <= u) {
      int i = l;
      while (true) {
        a[i] = 5;
        if (i == u) break;
        x = i;
        i++;
      }
    }
    return x;  // keep another phi live
  }

  /// CHECK-START: int Main.breakLoopReduction(int[]) induction_var_analysis (before)
  /// CHECK-DAG: <<Par:l\d+>>  ParameterValue                 loop:none
  /// CHECK-DAG: <<Zero:i\d+>> IntConstant 0                  loop:none
  /// CHECK-DAG: <<One:i\d+>>  IntConstant 1                  loop:none
  /// CHECK-DAG: <<Nil:l\d+>>  NullCheck [<<Par>>]                 loop:none
  /// CHECK-DAG: <<Red:i\d+>>  Phi [<<Zero>>,<<RedI:i\d+>>]   loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<Phi:i\d+>>  Phi [<<Zero>>,<<AddI:i\d+>>]   loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>  BoundsCheck [<<Phi>>,{{i\d+}}] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Get:i\d+>>  ArrayGet [<<Nil>>,<<Bnd>>]     loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<RedI>>      Add [<<Red>>,<<Get>>]          loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<NE:z\d+>>   NotEqual [{{i\d+}},<<Phi>>]    loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               If [<<NE>>]                    loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>      Add [<<Phi>>,<<One>>]          loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Comb:i\d+>> Phi [<<Zero>>,<<RedI>>]        loop:none
  /// CHECK-DAG:               Return [<<Comb>>]              loop:none
  //
  /// CHECK-START: int Main.breakLoopReduction(int[]) induction_var_analysis (after)
  /// CHECK-DAG: <<Par:l\d+>>  ParameterValue                     loop:none
  /// CHECK-DAG: <<Zero:i\d+>> IntConstant 0                      loop:none
  /// CHECK-DAG: <<One:i\d+>>  IntConstant 1                      loop:none
  /// CHECK-DAG: <<Nil:l\d+>>  NullCheck [<<Par>>]                loop:none
  /// CHECK-DAG: <<Red:i\d+>>  Phi [<<Zero>>,<<RedI:i\d+>>]       loop:<<Loop:B\d+>> outer_loop:none
  /// CHECK-DAG: <<Phi:i\d+>>  Phi [<<Zero>>,<<AddI:i\d+>>]       loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<LE:z\d+>>   LessThanOrEqual [<<Phi>>,{{i\d+}}] loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG:               If [<<LE>>]                        loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Bnd:i\d+>>  BoundsCheck [<<Phi>>,{{i\d+}}]     loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Get:i\d+>>  ArrayGet [<<Nil>>,<<Bnd>>]         loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<RedI>>      Add [<<Red>>,<<Get>>]              loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<AddI>>      Add [<<Phi>>,<<One>>]              loop:<<Loop>>      outer_loop:none
  /// CHECK-DAG: <<Comb:i\d+>> Phi [<<Zero>>,<<Red>>]             loop:none
  /// CHECK-DAG:               Return [<<Comb>>]                  loop:none
  //
  /// CHECK-START-ARM64: int Main.breakLoopReduction(int[]) loop_optimization (after)
  /// CHECK-DAG: <<Par:l\d+>>   ParameterValue              loop:none
  /// CHECK-DAG: <<Zero:i\d+>>  IntConstant 0               loop:none
  /// CHECK-IF:     hasIsaFeature("sve")
  //
  ///     CHECK-DAG: <<Exp:d\d+>>   VecSetScalars [<<Zero>>,{{j\d+}}]     loop:none
  ///     CHECK-DAG: <<LoopP:j\d+>> VecPredWhile                          loop:<<Loop:B\d+>> outer_loop:none
  ///     CHECK-DAG: <<VPhi:d\d+>>  Phi [<<Exp>>,<<VAdd:d\d+>>]           loop:<<Loop>>      outer_loop:none
  ///     CHECK-DAG: <<VLoad:d\d+>> VecLoad                               loop:<<Loop>>      outer_loop:none
  ///     CHECK-DAG: <<VAdd>>       VecAdd [<<VPhi>>,<<VLoad>>,<<LoopP>>] loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-ELSE:
  //
  ///     CHECK-DAG: <<Exp:d\d+>>   VecSetScalars [<<Zero>>]    loop:none
  ///     CHECK-DAG: <<VPhi:d\d+>>  Phi [<<Exp>>,<<VAdd:d\d+>>] loop:<<Loop:B\d+>> outer_loop:none
  ///     CHECK-DAG: <<VLoad:d\d+>> VecLoad                     loop:<<Loop>>      outer_loop:none
  ///     CHECK-DAG: <<VAdd>>       VecAdd [<<VPhi>>,<<VLoad>>] loop:<<Loop>>      outer_loop:none
  //
  /// CHECK-FI:
  static int breakLoopReduction(int[] a) {
    int l = 0;
    int u = a.length - 1;
    int x = 0;
    if (l <= u) {
      int i = l;
      while (true) {
        x += a[i];
        if (i == u) break;
        i++;
      }
    }
    return x;
  }

  //
  // Test driver.
  //

  public static void main(String[] args) {
    int[] a = new int[100];

    expectEquals(99, breakLoop(a));
    for (int i = 0; i < a.length; i++) {
      expectEquals(1, a[i]);
    }

    expectEquals(0, breakLoopDown(a));
    for (int i = 0; i < a.length; i++) {
      expectEquals(2, a[i]);
    }

    expectEquals(Integer.MAX_VALUE - 1, breakLoopSafeConst(a));
    for (int i = 0; i < a.length; i++) {
      int e = i < 16 ? 3 : 2;
      expectEquals(e, a[i]);
    }

    expectEquals(Integer.MAX_VALUE, breakLoopUnsafeConst(a));
    for (int i = 0; i < a.length; i++) {
      int e = i < 16 ? 4 : 2;
      expectEquals(e, a[i]);
    }

    expectEquals(98, breakLoopNastyPhi(a));
    for (int i = 0; i < a.length; i++) {
      expectEquals(5, a[i]);
    }

    expectEquals(500, breakLoopReduction(a));

    System.out.println("passed");
  }

  private static void expectEquals(int expected, int result) {
    if (expected != result) {
      throw new Error("Expected: " + expected + ", found: " + result);
    }
  }
}

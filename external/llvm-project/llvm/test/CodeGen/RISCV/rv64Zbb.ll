; NOTE: Assertions have been autogenerated by utils/update_llc_test_checks.py
; RUN: llc -mtriple=riscv64 -verify-machineinstrs < %s \
; RUN:   | FileCheck %s -check-prefix=RV64I
; RUN: llc -mtriple=riscv64 -mattr=+experimental-b -verify-machineinstrs < %s \
; RUN:   | FileCheck %s -check-prefix=RV64IB
; RUN: llc -mtriple=riscv64 -mattr=+experimental-zbb -verify-machineinstrs < %s \
; RUN:   | FileCheck %s -check-prefix=RV64IBB

define signext i32 @slo_i32(i32 signext %a, i32 signext %b) nounwind {
; RV64I-LABEL: slo_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    sllw a0, a0, a1
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: slo_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    slow a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: slo_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    slow a0, a0, a1
; RV64IBB-NEXT:    ret
  %neg = xor i32 %a, -1
  %shl = shl i32 %neg, %b
  %neg1 = xor i32 %shl, -1
  ret i32 %neg1
}

define i64 @slo_i64(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: slo_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    sll a0, a0, a1
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: slo_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    slo a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: slo_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    slo a0, a0, a1
; RV64IBB-NEXT:    ret
  %neg = xor i64 %a, -1
  %shl = shl i64 %neg, %b
  %neg1 = xor i64 %shl, -1
  ret i64 %neg1
}

define signext i32 @sro_i32(i32 signext %a, i32 signext %b) nounwind {
; RV64I-LABEL: sro_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    srlw a0, a0, a1
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sro_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    srow a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sro_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    srow a0, a0, a1
; RV64IBB-NEXT:    ret
  %neg = xor i32 %a, -1
  %shr = lshr i32 %neg, %b
  %neg1 = xor i32 %shr, -1
  ret i32 %neg1
}

define i64 @sro_i64(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: sro_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    srl a0, a0, a1
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sro_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sro a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sro_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sro a0, a0, a1
; RV64IBB-NEXT:    ret
  %neg = xor i64 %a, -1
  %shr = lshr i64 %neg, %b
  %neg1 = xor i64 %shr, -1
  ret i64 %neg1
}

define signext i32 @sloi_i32(i32 signext %a) nounwind {
; RV64I-LABEL: sloi_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    slli a0, a0, 1
; RV64I-NEXT:    ori a0, a0, 1
; RV64I-NEXT:    sext.w a0, a0
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sloi_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sloiw a0, a0, 1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sloi_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sloiw a0, a0, 1
; RV64IBB-NEXT:    ret
  %neg = shl i32 %a, 1
  %neg12 = or i32 %neg, 1
  ret i32 %neg12
}

define i64 @sloi_i64(i64 %a) nounwind {
; RV64I-LABEL: sloi_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    slli a0, a0, 1
; RV64I-NEXT:    ori a0, a0, 1
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sloi_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sloi a0, a0, 1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sloi_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sloi a0, a0, 1
; RV64IBB-NEXT:    ret
  %neg = shl i64 %a, 1
  %neg12 = or i64 %neg, 1
  ret i64 %neg12
}

define signext i32 @sroi_i32(i32 signext %a) nounwind {
; RV64I-LABEL: sroi_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    srli a0, a0, 1
; RV64I-NEXT:    lui a1, 524288
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sroi_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sroiw a0, a0, 1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sroi_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sroiw a0, a0, 1
; RV64IBB-NEXT:    ret
  %neg = lshr i32 %a, 1
  %neg12 = or i32 %neg, -2147483648
  ret i32 %neg12
}

; This is similar to the type legalized version of sroiw but the mask is 0 in
; the upper bits instead of 1 so the result is not sign extended. Make sure we
; don't match it to sroiw.
define i64 @sroiw_bug(i64 %a) nounwind {
; RV64I-LABEL: sroiw_bug:
; RV64I:       # %bb.0:
; RV64I-NEXT:    srli a0, a0, 1
; RV64I-NEXT:    addi a1, zero, 1
; RV64I-NEXT:    slli a1, a1, 31
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sroiw_bug:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    srli a0, a0, 1
; RV64IB-NEXT:    sbseti a0, a0, 31
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sroiw_bug:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    srli a0, a0, 1
; RV64IBB-NEXT:    addi a1, zero, 1
; RV64IBB-NEXT:    slli a1, a1, 31
; RV64IBB-NEXT:    or a0, a0, a1
; RV64IBB-NEXT:    ret
  %neg = lshr i64 %a, 1
  %neg12 = or i64 %neg, 2147483648
  ret i64 %neg12
}

define i64 @sroi_i64(i64 %a) nounwind {
; RV64I-LABEL: sroi_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    srli a0, a0, 1
; RV64I-NEXT:    addi a1, zero, -1
; RV64I-NEXT:    slli a1, a1, 63
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sroi_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sroi a0, a0, 1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sroi_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sroi a0, a0, 1
; RV64IBB-NEXT:    ret
  %neg = lshr i64 %a, 1
  %neg12 = or i64 %neg, -9223372036854775808
  ret i64 %neg12
}

declare i32 @llvm.ctlz.i32(i32, i1)

define signext i32 @ctlz_i32(i32 signext %a) nounwind {
; RV64I-LABEL: ctlz_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    addi sp, sp, -16
; RV64I-NEXT:    sd ra, 8(sp)
; RV64I-NEXT:    beqz a0, .LBB9_2
; RV64I-NEXT:  # %bb.1: # %cond.false
; RV64I-NEXT:    srliw a1, a0, 1
; RV64I-NEXT:    slli a0, a0, 32
; RV64I-NEXT:    srli a0, a0, 32
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 2
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 4
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 8
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 16
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 32
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    srli a1, a0, 1
; RV64I-NEXT:    lui a2, 21845
; RV64I-NEXT:    addiw a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    and a1, a1, a2
; RV64I-NEXT:    sub a0, a0, a1
; RV64I-NEXT:    lui a1, 13107
; RV64I-NEXT:    addiw a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    and a2, a0, a1
; RV64I-NEXT:    srli a0, a0, 2
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    add a0, a2, a0
; RV64I-NEXT:    srli a1, a0, 4
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    lui a1, 3855
; RV64I-NEXT:    addiw a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    lui a1, 4112
; RV64I-NEXT:    addiw a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    call __muldi3
; RV64I-NEXT:    srli a0, a0, 56
; RV64I-NEXT:    addi a0, a0, -32
; RV64I-NEXT:    j .LBB9_3
; RV64I-NEXT:  .LBB9_2:
; RV64I-NEXT:    addi a0, zero, 32
; RV64I-NEXT:  .LBB9_3: # %cond.end
; RV64I-NEXT:    ld ra, 8(sp)
; RV64I-NEXT:    addi sp, sp, 16
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: ctlz_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    clzw a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: ctlz_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    clzw a0, a0
; RV64IBB-NEXT:    ret
  %1 = call i32 @llvm.ctlz.i32(i32 %a, i1 false)
  ret i32 %1
}

declare i64 @llvm.ctlz.i64(i64, i1)

define i64 @ctlz_i64(i64 %a) nounwind {
; RV64I-LABEL: ctlz_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    addi sp, sp, -16
; RV64I-NEXT:    sd ra, 8(sp)
; RV64I-NEXT:    beqz a0, .LBB10_2
; RV64I-NEXT:  # %bb.1: # %cond.false
; RV64I-NEXT:    srli a1, a0, 1
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 2
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 4
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 8
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 16
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 32
; RV64I-NEXT:    or a0, a0, a1
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    srli a1, a0, 1
; RV64I-NEXT:    lui a2, 21845
; RV64I-NEXT:    addiw a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    and a1, a1, a2
; RV64I-NEXT:    sub a0, a0, a1
; RV64I-NEXT:    lui a1, 13107
; RV64I-NEXT:    addiw a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    and a2, a0, a1
; RV64I-NEXT:    srli a0, a0, 2
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    add a0, a2, a0
; RV64I-NEXT:    srli a1, a0, 4
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    lui a1, 3855
; RV64I-NEXT:    addiw a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    lui a1, 4112
; RV64I-NEXT:    addiw a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    call __muldi3
; RV64I-NEXT:    srli a0, a0, 56
; RV64I-NEXT:    j .LBB10_3
; RV64I-NEXT:  .LBB10_2:
; RV64I-NEXT:    addi a0, zero, 64
; RV64I-NEXT:  .LBB10_3: # %cond.end
; RV64I-NEXT:    ld ra, 8(sp)
; RV64I-NEXT:    addi sp, sp, 16
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: ctlz_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    clz a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: ctlz_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    clz a0, a0
; RV64IBB-NEXT:    ret
  %1 = call i64 @llvm.ctlz.i64(i64 %a, i1 false)
  ret i64 %1
}

declare i32 @llvm.cttz.i32(i32, i1)

define signext i32 @cttz_i32(i32 signext %a) nounwind {
; RV64I-LABEL: cttz_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    addi sp, sp, -16
; RV64I-NEXT:    sd ra, 8(sp)
; RV64I-NEXT:    beqz a0, .LBB11_2
; RV64I-NEXT:  # %bb.1: # %cond.false
; RV64I-NEXT:    addi a1, a0, -1
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 1
; RV64I-NEXT:    lui a2, 21845
; RV64I-NEXT:    addiw a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    and a1, a1, a2
; RV64I-NEXT:    sub a0, a0, a1
; RV64I-NEXT:    lui a1, 13107
; RV64I-NEXT:    addiw a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    and a2, a0, a1
; RV64I-NEXT:    srli a0, a0, 2
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    add a0, a2, a0
; RV64I-NEXT:    srli a1, a0, 4
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    lui a1, 3855
; RV64I-NEXT:    addiw a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    lui a1, 4112
; RV64I-NEXT:    addiw a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    call __muldi3
; RV64I-NEXT:    srli a0, a0, 56
; RV64I-NEXT:    j .LBB11_3
; RV64I-NEXT:  .LBB11_2:
; RV64I-NEXT:    addi a0, zero, 32
; RV64I-NEXT:  .LBB11_3: # %cond.end
; RV64I-NEXT:    ld ra, 8(sp)
; RV64I-NEXT:    addi sp, sp, 16
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: cttz_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    ctzw a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: cttz_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    ctzw a0, a0
; RV64IBB-NEXT:    ret
  %1 = call i32 @llvm.cttz.i32(i32 %a, i1 false)
  ret i32 %1
}

declare i64 @llvm.cttz.i64(i64, i1)

define i64 @cttz_i64(i64 %a) nounwind {
; RV64I-LABEL: cttz_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    addi sp, sp, -16
; RV64I-NEXT:    sd ra, 8(sp)
; RV64I-NEXT:    beqz a0, .LBB12_2
; RV64I-NEXT:  # %bb.1: # %cond.false
; RV64I-NEXT:    addi a1, a0, -1
; RV64I-NEXT:    not a0, a0
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 1
; RV64I-NEXT:    lui a2, 21845
; RV64I-NEXT:    addiw a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    and a1, a1, a2
; RV64I-NEXT:    sub a0, a0, a1
; RV64I-NEXT:    lui a1, 13107
; RV64I-NEXT:    addiw a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    and a2, a0, a1
; RV64I-NEXT:    srli a0, a0, 2
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    add a0, a2, a0
; RV64I-NEXT:    srli a1, a0, 4
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    lui a1, 3855
; RV64I-NEXT:    addiw a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    lui a1, 4112
; RV64I-NEXT:    addiw a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    call __muldi3
; RV64I-NEXT:    srli a0, a0, 56
; RV64I-NEXT:    j .LBB12_3
; RV64I-NEXT:  .LBB12_2:
; RV64I-NEXT:    addi a0, zero, 64
; RV64I-NEXT:  .LBB12_3: # %cond.end
; RV64I-NEXT:    ld ra, 8(sp)
; RV64I-NEXT:    addi sp, sp, 16
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: cttz_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    ctz a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: cttz_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    ctz a0, a0
; RV64IBB-NEXT:    ret
  %1 = call i64 @llvm.cttz.i64(i64 %a, i1 false)
  ret i64 %1
}

declare i32 @llvm.ctpop.i32(i32)

define signext i32 @ctpop_i32(i32 signext %a) nounwind {
; RV64I-LABEL: ctpop_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    addi sp, sp, -16
; RV64I-NEXT:    sd ra, 8(sp)
; RV64I-NEXT:    slli a1, a0, 32
; RV64I-NEXT:    srli a1, a1, 32
; RV64I-NEXT:    srliw a0, a0, 1
; RV64I-NEXT:    lui a2, 349525
; RV64I-NEXT:    addiw a2, a2, 1365
; RV64I-NEXT:    and a0, a0, a2
; RV64I-NEXT:    sub a0, a1, a0
; RV64I-NEXT:    srli a1, a0, 2
; RV64I-NEXT:    lui a2, 13107
; RV64I-NEXT:    addiw a2, a2, 819
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 819
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 819
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 819
; RV64I-NEXT:    and a1, a1, a2
; RV64I-NEXT:    and a0, a0, a2
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    srli a1, a0, 4
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    lui a1, 3855
; RV64I-NEXT:    addiw a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    lui a1, 4112
; RV64I-NEXT:    addiw a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    call __muldi3
; RV64I-NEXT:    srli a0, a0, 56
; RV64I-NEXT:    ld ra, 8(sp)
; RV64I-NEXT:    addi sp, sp, 16
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: ctpop_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    pcntw a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: ctpop_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    pcntw a0, a0
; RV64IBB-NEXT:    ret
  %1 = call i32 @llvm.ctpop.i32(i32 %a)
  ret i32 %1
}

declare i64 @llvm.ctpop.i64(i64)

define i64 @ctpop_i64(i64 %a) nounwind {
; RV64I-LABEL: ctpop_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    addi sp, sp, -16
; RV64I-NEXT:    sd ra, 8(sp)
; RV64I-NEXT:    srli a1, a0, 1
; RV64I-NEXT:    lui a2, 21845
; RV64I-NEXT:    addiw a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    slli a2, a2, 12
; RV64I-NEXT:    addi a2, a2, 1365
; RV64I-NEXT:    and a1, a1, a2
; RV64I-NEXT:    sub a0, a0, a1
; RV64I-NEXT:    lui a1, 13107
; RV64I-NEXT:    addiw a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 819
; RV64I-NEXT:    and a2, a0, a1
; RV64I-NEXT:    srli a0, a0, 2
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    add a0, a2, a0
; RV64I-NEXT:    srli a1, a0, 4
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    lui a1, 3855
; RV64I-NEXT:    addiw a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, 241
; RV64I-NEXT:    slli a1, a1, 12
; RV64I-NEXT:    addi a1, a1, -241
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    lui a1, 4112
; RV64I-NEXT:    addiw a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    slli a1, a1, 16
; RV64I-NEXT:    addi a1, a1, 257
; RV64I-NEXT:    call __muldi3
; RV64I-NEXT:    srli a0, a0, 56
; RV64I-NEXT:    ld ra, 8(sp)
; RV64I-NEXT:    addi sp, sp, 16
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: ctpop_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    pcnt a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: ctpop_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    pcnt a0, a0
; RV64IBB-NEXT:    ret
  %1 = call i64 @llvm.ctpop.i64(i64 %a)
  ret i64 %1
}

define signext i32 @sextb_i32(i32 signext %a) nounwind {
; RV64I-LABEL: sextb_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    slli a0, a0, 56
; RV64I-NEXT:    srai a0, a0, 56
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sextb_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sext.b a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sextb_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sext.b a0, a0
; RV64IBB-NEXT:    ret
  %shl = shl i32 %a, 24
  %shr = ashr exact i32 %shl, 24
  ret i32 %shr
}

define i64 @sextb_i64(i64 %a) nounwind {
; RV64I-LABEL: sextb_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    slli a0, a0, 56
; RV64I-NEXT:    srai a0, a0, 56
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sextb_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sext.b a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sextb_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sext.b a0, a0
; RV64IBB-NEXT:    ret
  %shl = shl i64 %a, 56
  %shr = ashr exact i64 %shl, 56
  ret i64 %shr
}

define signext i32 @sexth_i32(i32 signext %a) nounwind {
; RV64I-LABEL: sexth_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    slli a0, a0, 48
; RV64I-NEXT:    srai a0, a0, 48
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sexth_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sext.h a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sexth_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sext.h a0, a0
; RV64IBB-NEXT:    ret
  %shl = shl i32 %a, 16
  %shr = ashr exact i32 %shl, 16
  ret i32 %shr
}

define i64 @sexth_i64(i64 %a) nounwind {
; RV64I-LABEL: sexth_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    slli a0, a0, 48
; RV64I-NEXT:    srai a0, a0, 48
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: sexth_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sext.h a0, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: sexth_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sext.h a0, a0
; RV64IBB-NEXT:    ret
  %shl = shl i64 %a, 48
  %shr = ashr exact i64 %shl, 48
  ret i64 %shr
}

define signext i32 @min_i32(i32 signext %a, i32 signext %b) nounwind {
; RV64I-LABEL: min_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    blt a0, a1, .LBB19_2
; RV64I-NEXT:  # %bb.1:
; RV64I-NEXT:    mv a0, a1
; RV64I-NEXT:  .LBB19_2:
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: min_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    min a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: min_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    min a0, a0, a1
; RV64IBB-NEXT:    ret
  %cmp = icmp slt i32 %a, %b
  %cond = select i1 %cmp, i32 %a, i32 %b
  ret i32 %cond
}

define i64 @min_i64(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: min_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    blt a0, a1, .LBB20_2
; RV64I-NEXT:  # %bb.1:
; RV64I-NEXT:    mv a0, a1
; RV64I-NEXT:  .LBB20_2:
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: min_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    min a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: min_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    min a0, a0, a1
; RV64IBB-NEXT:    ret
  %cmp = icmp slt i64 %a, %b
  %cond = select i1 %cmp, i64 %a, i64 %b
  ret i64 %cond
}

define signext i32 @max_i32(i32 signext %a, i32 signext %b) nounwind {
; RV64I-LABEL: max_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    blt a1, a0, .LBB21_2
; RV64I-NEXT:  # %bb.1:
; RV64I-NEXT:    mv a0, a1
; RV64I-NEXT:  .LBB21_2:
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: max_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    max a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: max_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    max a0, a0, a1
; RV64IBB-NEXT:    ret
  %cmp = icmp sgt i32 %a, %b
  %cond = select i1 %cmp, i32 %a, i32 %b
  ret i32 %cond
}

define i64 @max_i64(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: max_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    blt a1, a0, .LBB22_2
; RV64I-NEXT:  # %bb.1:
; RV64I-NEXT:    mv a0, a1
; RV64I-NEXT:  .LBB22_2:
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: max_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    max a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: max_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    max a0, a0, a1
; RV64IBB-NEXT:    ret
  %cmp = icmp sgt i64 %a, %b
  %cond = select i1 %cmp, i64 %a, i64 %b
  ret i64 %cond
}

define signext i32 @minu_i32(i32 signext %a, i32 signext %b) nounwind {
; RV64I-LABEL: minu_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    bltu a0, a1, .LBB23_2
; RV64I-NEXT:  # %bb.1:
; RV64I-NEXT:    mv a0, a1
; RV64I-NEXT:  .LBB23_2:
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: minu_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    minu a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: minu_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    minu a0, a0, a1
; RV64IBB-NEXT:    ret
  %cmp = icmp ult i32 %a, %b
  %cond = select i1 %cmp, i32 %a, i32 %b
  ret i32 %cond
}

define i64 @minu_i64(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: minu_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    bltu a0, a1, .LBB24_2
; RV64I-NEXT:  # %bb.1:
; RV64I-NEXT:    mv a0, a1
; RV64I-NEXT:  .LBB24_2:
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: minu_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    minu a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: minu_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    minu a0, a0, a1
; RV64IBB-NEXT:    ret
  %cmp = icmp ult i64 %a, %b
  %cond = select i1 %cmp, i64 %a, i64 %b
  ret i64 %cond
}

define signext i32 @maxu_i32(i32 signext %a, i32 signext %b) nounwind {
; RV64I-LABEL: maxu_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    bltu a1, a0, .LBB25_2
; RV64I-NEXT:  # %bb.1:
; RV64I-NEXT:    mv a0, a1
; RV64I-NEXT:  .LBB25_2:
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: maxu_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    maxu a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: maxu_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    maxu a0, a0, a1
; RV64IBB-NEXT:    ret
  %cmp = icmp ugt i32 %a, %b
  %cond = select i1 %cmp, i32 %a, i32 %b
  ret i32 %cond
}

define i64 @maxu_i64(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: maxu_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    bltu a1, a0, .LBB26_2
; RV64I-NEXT:  # %bb.1:
; RV64I-NEXT:    mv a0, a1
; RV64I-NEXT:  .LBB26_2:
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: maxu_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    maxu a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: maxu_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    maxu a0, a0, a1
; RV64IBB-NEXT:    ret
  %cmp = icmp ugt i64 %a, %b
  %cond = select i1 %cmp, i64 %a, i64 %b
  ret i64 %cond
}

declare i32 @llvm.abs.i32(i32, i1 immarg)

define i32 @abs_i32(i32 %x) {
; RV64I-LABEL: abs_i32:
; RV64I:       # %bb.0:
; RV64I-NEXT:    sext.w a0, a0
; RV64I-NEXT:    srai a1, a0, 63
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    xor a0, a0, a1
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: abs_i32:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    sext.w a0, a0
; RV64IB-NEXT:    neg a1, a0
; RV64IB-NEXT:    max a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: abs_i32:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    sext.w a0, a0
; RV64IBB-NEXT:    neg a1, a0
; RV64IBB-NEXT:    max a0, a0, a1
; RV64IBB-NEXT:    ret
  %abs = tail call i32 @llvm.abs.i32(i32 %x, i1 true)
  ret i32 %abs
}

declare i64 @llvm.abs.i64(i64, i1 immarg)

define i64 @abs_i64(i64 %x) {
; RV64I-LABEL: abs_i64:
; RV64I:       # %bb.0:
; RV64I-NEXT:    srai a1, a0, 63
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    xor a0, a0, a1
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: abs_i64:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    neg a1, a0
; RV64IB-NEXT:    max a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: abs_i64:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    neg a1, a0
; RV64IBB-NEXT:    max a0, a0, a1
; RV64IBB-NEXT:    ret
  %abs = tail call i64 @llvm.abs.i64(i64 %x, i1 true)
  ret i64 %abs
}

; We select a i32 addi that zero-extends the result on RV64 as addiwu

define zeroext i32 @zext_add_to_addiwu(i32 signext %a) nounwind {
; RV64I-LABEL: zext_add_to_addiwu:
; RV64I:       # %bb.0:
; RV64I-NEXT:    addi a0, a0, 1
; RV64I-NEXT:    slli a0, a0, 32
; RV64I-NEXT:    srli a0, a0, 32
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: zext_add_to_addiwu:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    addiwu a0, a0, 1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: zext_add_to_addiwu:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    addiwu a0, a0, 1
; RV64IBB-NEXT:    ret
  %add = add i32 %a, 1
  ret i32 %add
}

define i64 @addiwu(i64 %a) nounwind {
; RV64I-LABEL: addiwu:
; RV64I:       # %bb.0:
; RV64I-NEXT:    addi a0, a0, 1
; RV64I-NEXT:    slli a0, a0, 32
; RV64I-NEXT:    srli a0, a0, 32
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: addiwu:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    addiwu a0, a0, 1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: addiwu:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    addiwu a0, a0, 1
; RV64IBB-NEXT:    ret
  %conv = add i64 %a, 1
  %conv1 = and i64 %conv, 4294967295
  ret i64 %conv1
}

define i64 @slliuw(i64 %a) nounwind {
; RV64I-LABEL: slliuw:
; RV64I:       # %bb.0:
; RV64I-NEXT:    slli a0, a0, 1
; RV64I-NEXT:    addi a1, zero, 1
; RV64I-NEXT:    slli a1, a1, 33
; RV64I-NEXT:    addi a1, a1, -2
; RV64I-NEXT:    and a0, a0, a1
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: slliuw:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    slliu.w a0, a0, 1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: slliuw:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    slliu.w a0, a0, 1
; RV64IBB-NEXT:    ret
  %conv1 = shl i64 %a, 1
  %shl = and i64 %conv1, 8589934590
  ret i64 %shl
}

; We select a i32 add that zero-extends the result on RV64 as addwu

define zeroext i32 @zext_add_to_addwu(i32 signext %a, i32 signext %b) nounwind {
; RV64I-LABEL: zext_add_to_addwu:
; RV64I:       # %bb.0:
; RV64I-NEXT:    add a0, a0, a1
; RV64I-NEXT:    slli a0, a0, 32
; RV64I-NEXT:    srli a0, a0, 32
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: zext_add_to_addwu:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    addwu a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: zext_add_to_addwu:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    addwu a0, a0, a1
; RV64IBB-NEXT:    ret
  %add = add i32 %a, %b
  ret i32 %add
}

define i64 @addwu(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: addwu:
; RV64I:       # %bb.0:
; RV64I-NEXT:    add a0, a1, a0
; RV64I-NEXT:    slli a0, a0, 32
; RV64I-NEXT:    srli a0, a0, 32
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: addwu:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    addwu a0, a1, a0
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: addwu:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    addwu a0, a1, a0
; RV64IBB-NEXT:    ret
  %add = add i64 %b, %a
  %conv1 = and i64 %add, 4294967295
  ret i64 %conv1
}

; We select a i32 sub that zero-extends the result on RV64 as subwu

define zeroext i32 @zext_sub_to_subwu(i32 signext %a, i32 signext %b) nounwind {
; RV64I-LABEL: zext_sub_to_subwu:
; RV64I:       # %bb.0:
; RV64I-NEXT:    sub a0, a0, a1
; RV64I-NEXT:    slli a0, a0, 32
; RV64I-NEXT:    srli a0, a0, 32
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: zext_sub_to_subwu:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    subwu a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: zext_sub_to_subwu:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    subwu a0, a0, a1
; RV64IBB-NEXT:    ret
  %sub = sub i32 %a, %b
  ret i32 %sub
}

define i64 @subwu(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: subwu:
; RV64I:       # %bb.0:
; RV64I-NEXT:    sub a0, a0, a1
; RV64I-NEXT:    slli a0, a0, 32
; RV64I-NEXT:    srli a0, a0, 32
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: subwu:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    subwu a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: subwu:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    subwu a0, a0, a1
; RV64IBB-NEXT:    ret
  %sub = sub i64 %a, %b
  %conv1 = and i64 %sub, 4294967295
  ret i64 %conv1
}

define i64 @adduw(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: adduw:
; RV64I:       # %bb.0:
; RV64I-NEXT:    slli a1, a1, 32
; RV64I-NEXT:    srli a1, a1, 32
; RV64I-NEXT:    add a0, a1, a0
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: adduw:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    addu.w a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: adduw:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    addu.w a0, a0, a1
; RV64IBB-NEXT:    ret
  %and = and i64 %b, 4294967295
  %add = add i64 %and, %a
  ret i64 %add
}

define i64 @subuw(i64 %a, i64 %b) nounwind {
; RV64I-LABEL: subuw:
; RV64I:       # %bb.0:
; RV64I-NEXT:    slli a1, a1, 32
; RV64I-NEXT:    srli a1, a1, 32
; RV64I-NEXT:    sub a0, a0, a1
; RV64I-NEXT:    ret
;
; RV64IB-LABEL: subuw:
; RV64IB:       # %bb.0:
; RV64IB-NEXT:    subu.w a0, a0, a1
; RV64IB-NEXT:    ret
;
; RV64IBB-LABEL: subuw:
; RV64IBB:       # %bb.0:
; RV64IBB-NEXT:    subu.w a0, a0, a1
; RV64IBB-NEXT:    ret
  %and = and i64 %b, 4294967295
  %sub = sub i64 %a, %and
  ret i64 %sub
}

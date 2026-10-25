.syntax unified
.thumb
.section .text
.global _start
_start:
    bne.w tgt
    .fill 0x86, 1, 0
tgt:

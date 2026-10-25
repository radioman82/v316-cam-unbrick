.syntax unified
.thumb
.section .text
.global _start
_start:
    b.w tgt
    .fill 428, 1, 0
tgt:

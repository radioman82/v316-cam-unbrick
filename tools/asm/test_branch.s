
.syntax unified
.thumb
.text
target:
    nop
.space 0x99c
source:
    beq.w target

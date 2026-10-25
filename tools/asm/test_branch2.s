
.syntax unified
.thumb
.text
target:
    nop
.space 0x99e
source:
    beq.w target

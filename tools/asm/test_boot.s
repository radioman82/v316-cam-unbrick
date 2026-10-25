
.syntax unified
.thumb
.global _start
.text
.org 0x6c0ee
_start:
    ldr.w r0, [r0, #0x114]
    ldr r3, [r0, #0]
    ldr r3, [r3, #108]
    add sp, #12
    ldmia.w sp!, {r4, r5, lr}
    bx r3

.syntax unified
.thumb
.section .text.original_preview_post,"ax",%progbits
.global original_preview_post
.thumb_func
original_preview_post:
    push.w {r0,r1,r2,r4,r5,r6,r7,r8,r9,lr}
    ldr pc, =0x5aa0d
.section .text.original_preview_key,"ax",%progbits
.global original_preview_key
.thumb_func
original_preview_key:
    push {r4-r7,lr}
    sub sp, #20
    ldr pc, =0x5b841
.section .text.original_window_proc,"ax",%progbits
.global original_window_proc
.thumb_func
original_window_proc:
    cmp r1, #0x61
    push.w {r4,r5,r6,r7,r8,r9,lr}
    ldr pc, =0x5718b
.section .text.division,"ax",%progbits
.global __aeabi_idiv
.thumb_func
__aeabi_idiv:
    ldr pc, =0x1cf24
.global __aeabi_uidiv
.thumb_func
__aeabi_uidiv:
    ldr pc, =0x1cef4
.section .text.startup_menu,"ax",%progbits
.global startup_menu_entry
.thumb_func
startup_menu_entry:
    mov r0, r4
    bl theme_startup_window_loaded
    b.w 0x6c0fe

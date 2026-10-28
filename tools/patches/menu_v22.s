    .syntax unified
    .thumb
    .org 0x5afe4
    .global front_toggle
front_toggle:
    mov r0, r4
    bl dismiss_prompt
    mov r0, r4
    bl 0x5a658
    cmp r0, #1
    beq front_closed
    cmp r0, #7
    beq front_closed
    b.w 0x24ad70
front_closed:
    add sp, #20
    pop {r4-r7, pc}

    .org 0x5b000
    .global show_modes
show_modes:
    push {r4, lr}
    mov r4, r0
    ldr.w r0, [r0, #0xec]
    ldr.w r1, [r0, #0x118]
    cmp r1, #4
    blo show_modes_ready
    subs r1, #4
    str.w r1, [r0, #0x118]
    movs r1, #4
    strb.w r1, [r0, #0x11d]
    bl 0x67746
show_modes_ready:
    mov r0, r4
    pop.w {r4, lr}
    b.w 0x5a6f4

    .org 0x24ad84
    .global select_local_mode
select_local_mode:
    ldrb.w r3, [r0, #0x11d]
    cmp r3, #4
    bne select_original
    cmp r1, #4
    it ge
    subge r1, r1, #4
select_original:
    push {r3-r5, lr}
    mov r4, r0
    b.w 0x66dc8
    .org 0x24ada0
    .global tile_dispatch
tile_dispatch:
    push {r4-r6, lr}
    mov r4, r0
    mov r5, r2
    cmp r5, #3
    beq setup
    ldr.w r0, [r4, #0x114]
    bl 0x697ac
    movs r6, #0
    cmp r5, #0
    it eq
    moveq r6, #4
    ldr.w r0, [r4, #0xec]
    strb.w r6, [r0, #0x11d]
    movs r1, #0
    str.w r1, [r0, #0x118]
    bl 0x67746
    mov r0, r4
    mov r2, r6
    bl 0x5ab54
    mov r0, r4
    bl 0x5a6f4
    cmp r5, #2
    bne done
    movw r0, #0x32a2
    movt r0, #0x20
    blx 0x1c94c
done:
    pop {r4-r6, pc}
setup:
    mov r0, r4
    movs r1, #1
    bl 0x5aeac
    pop {r4-r6, pc}

    .balign 4
    .global remote_key
remote_key:
    cmp r1, #60
    beq remote_modes
    cmp r1, #61
    beq dismiss_prompt
    /* Original keyProc prologue; the following PC-relative load stays in place. */
    push {r4-r7, lr}
    sub sp, #20
    b.w 0x5b840
remote_modes:
    push {r4, lr}
    mov r4, r0
    bl dismiss_prompt
    mov r0, r4
    bl show_modes
    pop {r4, pc}

    .global dismiss_prompt
dismiss_prompt:
    ldr.w r0, [r0, #0xe8]
    cbz r0, dismiss_done
    ldr r3, [r0]
    ldr r3, [r3, #0x1c]
    bx r3
dismiss_done:
    bx lr

    .balign 4
    .global filter_modes
filter_modes:
    /* Called in ModelSelectWindow::Init, r4=model, r0=list, r1=vector. */
    ldrb.w r2, [r4, #0x11d]
    push {r4-r6, lr}
    mov r4, r1
    ldr r5, [r1]
    ldr r6, [r1, #4]
    subs r3, r6, r5
    cmp r3, #160
    bne filter_call
    cmp r2, #4
    bne filter_video
    add.w r3, r5, #80
    str r3, [r1]
    b filter_call
filter_video:
    add.w r3, r5, #80
    str r3, [r1, #4]
filter_call:
    ldr r3, [r0]
    ldr r3, [r3, #0x68]
    blx r3
    /* Restore ownership before the original code frees the vector. */
    str r5, [r4]
    str r6, [r4, #4]
    pop {r4-r6, pc}

    .balign 4
    .global mode_callback
mode_callback:
    ldr.w r3, [r0, #0xec]
    ldrb.w r3, [r3, #0x11d]
    cmp r3, #4
    it eq
    addeq r2, r2, #4
    b.w 0x5ab54

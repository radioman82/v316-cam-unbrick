	.syntax unified
	.thumb
	.text
	.org 0x6c0ee
	.global boot_hook
boot_hook:
	ldr.w	r0, [r4, #0x114]   @ r0 = self->func_win (FunctionSelectWindow*)
	ldr	r3, [r0, #0]       @ r3 = vtable
	ldr	r3, [r3, #108]     @ r3 = FunctionSelectWindow::Show()
	add	sp, #12
	ldmia.w	sp!, {r4, r5, lr}  @ restore frame, lr = return addr of OnWindowLoaded
	bx	r3                 @ tail-call Show() -> returns to OnWindowLoaded's caller

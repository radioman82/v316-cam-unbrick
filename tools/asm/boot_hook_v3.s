	.syntax unified
	.thumb
	.text
	.org 0x6c0ee
	.global boot_hook
boot_hook:
	mov	r0, r4              @ FIX: KeyFunctionProc expects self in r0
	add	sp, #12
	ldmia.w	sp!, {r4, r5, lr}
	b.w	0x5b030             @ -> KeyFunctionProc -> FunctionSelectWindow::Show()
	nop
	nop

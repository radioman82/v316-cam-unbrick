	.syntax unified
	.thumb
	.text

	@ Front button (KEY_POWER 116 -> app key 132) in the preview window:
	@ call FunctionSelectWindow::Show() directly through a code cave.
	@ Bypasses the KeyFunctionProc guards (0x5b060/0x5b07a/0x5b080/0x5b086).
	.org 0x5ba46
	b.w	0x1f5130

	.org 0x1f5130
	ldr.w	r0, [r0, #0x114]    @ r0 = self->func_win   (r0 still holds self here)
	ldr	r3, [r0, #0]
	ldr	r3, [r3, #108]      @ FunctionSelectWindow::Show()
	bx	r3                  @ tail call; lr was restored at 0x5ba42

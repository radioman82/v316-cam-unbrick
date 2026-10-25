	.syntax unified
	.thumb
	.text

	@ Front button (key 132) in the preview window: replace the tail call with a
	@ jump into a code cave that calls FunctionSelectWindow::Show() directly,
	@ bypassing the KeyFunctionProc guards that abort on cold/odd states.
	.org 0x5ba46
	b.w	0x1f5130

	.org 0x1f5130
stub:
	push	{r0, lr}            @ r0 = self (preview presenter)
	adr	r0, keystr
	blx	0x1c94c             @ system("touch /tmp/KEYHIT")  -> path marker
	pop	{r0, lr}
	ldr.w	r0, [r0, #0x114]    @ r0 = self->func_win
	ldr	r3, [r0, #0]
	ldr	r3, [r3, #108]      @ FunctionSelectWindow::Show()
	bx	r3                  @ tail call, lr already restored

keystr:
	.asciz	"touch /tmp/KEYHIT"
	.balign 4

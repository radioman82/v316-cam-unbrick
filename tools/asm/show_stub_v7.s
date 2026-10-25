	.syntax unified
	.thumb
	.text

	@ NOTE: .org directives must be in ascending order.

	@ ---------------------------------------------------------------
	@ B) Autostart: end of PreviewPresenter window-init
	@    (0x48608: mov r0,r4 / add sp,#248 / pop {r4,r5,r6,pc}).
	@    Here func_win is already created. r4 = self, lr is on the
	@    stack, so lr may be clobbered freely.
	@ ---------------------------------------------------------------
	.org 0x48608
	b.w	0x1f5140

	@ ---------------------------------------------------------------
	@ A) Front button (KEY_POWER 116 -> app key 132) in the preview
	@    window: call FunctionSelectWindow::Show() directly.
	@ ---------------------------------------------------------------
	.org 0x5ba46
	b.w	0x1f5130

	@ ---------------------------------------------------------------
	@ Cave: key handler stub
	@ ---------------------------------------------------------------
	.org 0x1f5130
key_stub:
	ldr.w	r0, [r0, #0x114]    @ r0 = self->func_win
	ldr	r3, [r0, #0]
	ldr	r3, [r3, #108]      @ Show()
	bx	r3                  @ tail call, lr already restored

	@ ---------------------------------------------------------------
	@ Cave: boot stub
	@ ---------------------------------------------------------------
	.org 0x1f5140
boot_stub:
	adr	r0, bootstr
	blx	0x1c94c             @ system("touch /tmp/BOOTHOOK") -> path marker
	ldr.w	r0, [r4, #0x114]
	cbz	r0, bail            @ window not created yet -> behave normally
	ldr	r3, [r0, #0]
	ldr	r3, [r3, #108]
	blx	r3                  @ Show() - normal call, returns here
bail:
	mov	r0, r4              @ restore return value
	add.w	sp, sp, #248        @ original epilogue
	pop.w	{r4, r5, r6, pc}

bootstr:
	.asciz	"touch /tmp/BOOTHOOK"
	.balign 4

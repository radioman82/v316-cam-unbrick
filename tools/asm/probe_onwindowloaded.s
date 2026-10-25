	@ Probe: ist [self+0x114] (FunctionSelectWindow) am Ende von
	@ PreviewWindow::OnWindowLoaded (preview.cpp, vaddr 0x6c0e8) gueltig?
	@ Schreibt /tmp/OL_OK bzw. /tmp/OL_NULL und fuehrt das Original aus.
	@ Adressregel: vaddr = datei_offset + 0x10000
	.syntax unified
	.thumb

	.org 0x6c0e8
	b.w	probe_ol

	.org 0x1f513c
probe_ol:
	push	{r0, r1, r2, r3, r12, lr}
	ldr.w	r1, [r4, #276]		@ 0x114 = FunctionSelectWindow*
	cbz	r1, p_null
	adr	r0, str_ok
	blx	0x1c94c			@ system()
	b	p_done
p_null:
	adr	r0, str_null
	blx	0x1c94c
p_done:
	pop	{r0, r1, r2, r3, r12, lr}

	@ Original ab 0x6c0e8: Fenster [r4+0x90] mit id 11 zeigen
	ldr.w	r0, [r4, #144]		@ 0x90
	cbz	r0, p_ret
	ldr	r3, [r0]
	movs	r2, #0
	movs	r1, #11
	ldr	r3, [r3, #120]		@ vtable-Slot 30
	blx	r3
p_ret:
	add	sp, #12
	pop	{r4, r5, pc}

	.align 2
str_ok:
	.asciz	"touch /tmp/OL_OK"
	.align 2
str_null:
	.asciz	"touch /tmp/OL_NULL"

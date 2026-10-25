	@ Autostart v2: 4-Kachel-Menue beim Booten anzeigen.
	@ Anker: Ende von PreviewWindow::OnWindowLoaded (preview.cpp, vaddr 0x6c0e8).
	@ Dort ist die UI fertig aufgebaut und [self+0x114] gueltig (Probe /tmp/OL_OK bestaetigt).
	@
	@ Ablauf:
	@   1. Original ausfuehren: Fenster [self+0x90] mit id 11 zeigen
	@   2. Einmal-Flag /tmp/as_done pruefen (access)
	@   3. falls nicht vorhanden: Flag anlegen und
	@      [self+0x114]->Show()  (FunctionSelectWindow, vtable-Slot 108)
	@
	@ Adressregel: vaddr = datei_offset + 0x10000
	.syntax unified
	.thumb

	.org 0x6c0e8
	b.w	autostart

	.org 0x1f513c
autostart:
	push	{r0, r1, r2, r3, r12, lr}

	@ --- Original: Fenster [r4+0x90] mit id 11 zeigen ---------------------
	ldr.w	r0, [r4, #144]		@ 0x90
	cbz	r0, as_guard
	ldr	r3, [r0]
	movs	r2, #0
	movs	r1, #11
	ldr	r3, [r3, #120]		@ vtable-Slot 30
	blx	r3

as_guard:
	@ --- Einmal-Flag -------------------------------------------------------
	adr	r0, path_done
	movs	r1, #0			@ F_OK
	blx	0x1cc3c			@ access()
	cbz	r0, as_ret		@ Flag existiert -> fertig
	adr	r0, cmd_touch
	blx	0x1c94c			@ system("touch /tmp/as_done")

	@ --- FunctionSelectWindow::Show() ------------------------------------
	ldr.w	r0, [r4, #276]		@ 0x114
	cbz	r0, as_ret
	ldr	r3, [r0]
	ldr	r3, [r3, #108]		@ vtable-Slot 27 = Show()
	blx	r3

as_ret:
	pop	{r0, r1, r2, r3, r12, lr}
	add	sp, #12
	pop	{r4, r5, pc}

	.align 2
path_done:
	.asciz	"/tmp/as_done"
	.align 2
cmd_touch:
	.asciz	"touch /tmp/as_done"

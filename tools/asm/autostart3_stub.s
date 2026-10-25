	@ Autostart v3: 4-Kachel-Menue beim Booten anzeigen.
	@
	@ Anker: Ende von PreviewWindow::OnWindowLoaded (preview.cpp, vaddr 0x6c0e8).
	@ Dort ist die UI fertig (Icons werden in function_select_window.cpp geladen).
	@
	@ Wichtig: r4 ist NICHT das PreviewWindow - [r4+0x114] ist dort Muell
	@ (Autostart v2 crashte bei 0x1f5166). Das PreviewWindow holen wir ueber
	@ [r4+0x90]: genau dieses Fenster zeigt der Originalcode mit id 11 an.
	@
	@ Ablauf:
	@   1. Original ausfuehren: Fenster [r4+0x90] mit id 11 zeigen
	@   2. Einmal-Flag /tmp/AS pruefen (access)
	@   3. falls nicht vorhanden: Flag anlegen und
	@      [[r4+0x90]+0x114]->Show()  ueber den bestehenden Show-Stub 0x1f5130
	@
	@ Adressregel: vaddr = datei_offset + 0x10000
	.syntax unified
	.thumb

	.org 0x6c0e8
	b.w	autostart

	.org 0x1f513c
autostart:
	push	{r0, r1, r2, r3, r7, r12, lr}

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
	blx	0x1c94c			@ system("touch /tmp/AS")

	@ --- Kachelfenster holen und zeigen -----------------------------------
	ldr.w	r0, [r4, #144]		@ PreviewWindow*
	cbz	r0, as_ret
	ldr.w	r7, [r0, #276]		@ 0x114 = FunctionSelectWindow*
	cbz	r7, as_ret
	movw	r3, #0x0000
	movt	r3, #0x0001		@ 0x00010000 = unterste plausible Adresse
	cmp	r7, r3
	blo	as_ret
	mov	r0, r7
	bl	0x1f5130		@ Show-Stub: ldr r0,[r0,#0x114] ... bx r3

as_ret:
	pop	{r0, r1, r2, r3, r7, r12, lr}
	add	sp, #12
	pop	{r4, r5, pc}

	.align 2
path_done:
	.asciz	"/tmp/AS"
	.align 2
cmd_touch:
	.asciz	"touch /tmp/AS"

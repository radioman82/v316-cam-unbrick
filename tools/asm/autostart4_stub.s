	@ Autostart v4: 4-Kachel-Menue beim Booten anzeigen.
	@
	@ Zwei Hooks, weil die Objekte getrennt sind:
	@   Hook 1 @ 0x6c0e8  Ende PreviewWindow::OnWindowLoaded (preview.cpp)
	@          -> setzt nur das Flag /tmp/A, wenn work mode <= 7
	@             ([r4+0x90] ist dort der WindowManager, NICHT das PreviewWindow;
	@              [r4+0x114] ist Muell -> Autostart v2 crashte bei 0x1f5166)
	@   Hook 2 @ 0x5ca28  Anfang PreviewWindow::HandleMessage (preview_window.cpp)
	@          -> hier ist r0 = PreviewWindow und [self+0x114] das
	@             FunctionSelectWindow. Flag konsumieren, dann Show().
	@
	@ Reihenfolge in Hook 2: erst Flag loeschen, dann Show() - sonst kann ein
	@ rekursiver HandleMessage-Aufruf aus Show() erneut Show() ausloesen.
	@
	@ Adressregel: vaddr = datei_offset + 0x10000
	.syntax unified
	.thumb

	@ ---------------------------------------------------------------- Hook 2
	.org 0x5ca28
	b.w	hook2

	@ ---------------------------------------------------------------- Hook 1
	.org 0x6c0e8
	b.w	hook1

	@ ------------------------------------------------------- Code-Cave 0x1f513c
	.org 0x1f513c

hook1:
	ldr	r3, [r4, #148]		@ 0x94 = work mode
	cmp	r3, #7
	bhi	1f			@ mode 8/9 = erste OnWindowLoaded-Runde, ignorieren
	adr	r0, cmd_touch
	blx	0x1c94c			@ system(">/tmp/A")
1:
	ldr	r0, [r4, #144]		@ 0x90 (Originalbefehl von 0x6c0e8)
	b.w	0x6c0ec			@ Rest des Original-Epilogs

	.align 2
cmd_touch:
	.asciz	">/tmp/A"

	.align 1			@ 2 Byte reichen: hook2 wird nur angesprungen
hook2:
	push.w	{r0, r1, r2, r3, r7, r12, lr}
	mov	r7, r0			@ r7 = PreviewWindow* (callee-saved)
	adr	r0, path_flag
	movs	r1, #0			@ F_OK
	blx	0x1cc3c			@ access()
	cbnz	r0, 2f			@ Flag fehlt -> nichts tun
	adr	r0, cmd_rm
	blx	0x1c94c			@ system("rm -f /tmp/A")  (erst entwaffnen!)
	ldr	r0, [r7, #276]		@ 0x114 = FunctionSelectWindow*
	cbz	r0, 2f
	mov	r0, r7
	bl	0x1f5130		@ Show-Stub
2:
	pop.w	{r0, r1, r2, r3, r7, r12, lr}
	push.w	{r4, r5, r6, r7, r8, r9, r10, r11, lr}	@ Original-Prolog 0x5ca28
	b.w	0x5ca2c

	.align 2
path_flag:
	.asciz	"/tmp/A"

	.align 2
cmd_rm:
	.asciz	"rm -f /tmp/A"

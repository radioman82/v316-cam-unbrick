	@ Autostart v5: 4-Kachel-Menue beim Booten anzeigen.
	@
	@ Zwei Hooks:
	@   Hook 1 @ 0x6c0e8  Ende PreviewWindow::OnWindowLoaded (preview.cpp)
	@          -> startet nur einen Hintergrund-Job, der nach 3 s das Flag
	@             /tmp/A anlegt. Kein Show() hier: die Kachel-Ressourcen sind
	@             erst ~1,4 s nach dieser Stelle geladen (function_select_window.cpp:129),
	@             vorher crasht Show() (0x56d32).
	@   Hook 2 @ 0x5ca28  Anfang PreviewWindow::HandleMessage (preview_window.cpp)
	@          -> hier ist r0 = PreviewWindow und [self+0x114] das
	@             FunctionSelectWindow. Flag konsumieren, dann Show().
	@
	@ /tmp ist tmpfs (RAM) -> Flag ueberlebt keinen Reboot.
	@ Reihenfolge in Hook 2: erst entwaffnen, dann Show() - sonst kann ein
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
	adr	r0, cmd_bg
	blx	0x1c94c			@ system("(sleep 3;mkdir /tmp/A)&")
	ldr	r0, [r4, #144]		@ 0x90 (Originalbefehl von 0x6c0e8)
	b.w	0x6c0ec			@ Rest des Original-Epilogs

hook2:
	push.w	{r0, r1, r2, r3, r7, r12, lr}
	mov	r7, r0			@ r7 = PreviewWindow* (callee-saved)
	adr	r0, path_flag		@ = "/tmp/A" innerhalb cmd_bg
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

	@ String-Block: 4-Byte-ausgerichtet, damit `adr` (imm8*4) mit 2 Byte reicht.
	@ Das Doppel-Leerzeichen in cmd_bg legt "/tmp/A" auf Offset 16 (4-aligned),
	@ dadurch wird kein eigener "/tmp/A"-String gebraucht.
	.align 2
cmd_rm:
	.asciz	"rm -f /tmp/A"			@ 13 Byte, dann 3 Byte Fuellung
	.align 2
cmd_bg:
	.ascii	"(sleep 3;mkdir  "
path_flag:
	.asciz	"/tmp/A)&"

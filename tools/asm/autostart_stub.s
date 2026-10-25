@ Autostart: Skript starten, das nach dem Boot einen synthetischen KEY_POWER
@ einspeist. Das Skript oeffnet ueber den bestehenden Patch D die 4 Kacheln.
@
@ Hook: 0x5caee  (MSG_MODE_SWITCH_DONE-Zweig in PreviewWindow::HandleMessage)
@        r0 = self (Presenter), r6 = msg-Daten
@ Stub: 0x1f5140 (Code-Cave in .rodata, ausfuehrbares PT_LOAD-Segment)
@
@ Einmal-Sperre: /tmp/as_done (tmpfs). Wird im selben system()-Aufruf angelegt,
@ damit ein zweiter Aufruf nicht erneut startet.
@
@ WICHTIG: Show() darf hier NICHT direkt aufgerufen werden - MSG_MODE_SWITCH_DONE
@ wird zugestellt, waehrend die Fenster noch aufgebaut werden (Absturz bei 0x56d32).

.syntax unified
.thumb

.org 0x5caee
b.w	autostart

.org 0x1f5140
autostart:
	push	{r0, r1, r2, r3, r7, r8, r12, lr}
	ldr.w	r7, [r0, #0x114]	@ FunctionSelectWindow* (nur als Gueltigkeitsprobe)
	cbz	r7, as_done
	adr	r0, path_done
	movs	r1, #0			@ F_OK
	blx	0x1cc3c			@ access()
	cbz	r0, as_done		@ Marker existiert -> bereits gestartet
	adr	r0, cmd_run
	blx	0x1c94c			@ system()
as_done:
	pop	{r0, r1, r2, r3, r7, r8, r12, lr}
	str.w	r6, [r0, #372]		@ Original-Instruktion
	b.w	0x5caf2			@ weiter im Originalcode

.align 2
path_done:
	.asciz	"/tmp/as_done"
.align 2
cmd_run:
	.asciz	"touch /tmp/as_done; /mnt/extsd/as.sh &"

	@ 4-Kachel-Dispatcher — Ersatz fuer PreviewWindow::FunctionChangeProc
	@ vaddr 0x5afe0, Slot 0x5afe0..0x5b030 (80 B)
	@
	@ Signatur wie Original: (r0 = self = PreviewWindow, r1 = ?, r2 = Kachelindex)
	@
	@   0 = FOTO    -> PostMsg(self, self, 69, 0)   [Modus 5 = normal_pic]
	@   1 = VIDEO   -> PostMsg(self, self, 64, 0)   [Modus 0 = normal_rec]
	@   2 = STREAM  -> system("/mnt/extsd/start_streaming.sh &")
	@   3 = SETUP   -> BottomBarFunctionProc(self, 1)   (bewaehrt, schliesst selbst)
	@
	@ Warum PostMsg und nicht ChangeWorkMode direkt:
	@   ChangeWorkMode (0x6bd68) synchron im Tasten-Handler aufzurufen hat in v7
	@   zum Absturz gefuehrt. Die Stock-Firmware arbeitet ausschliesslich ueber
	@   PostMsg (0x5aa08) — die Nachricht wird in die Queue gelegt und erst
	@   nach dem Verlassen des Tasten-Handlers verarbeitet. Genau dieser Weg
	@   wird hier benutzt.
	@
	@ Herkunft der Nachrichtennummern:
	@   Modus-Select-Fenster -> PreviewWindow::ModeChangeProc (vaddr 0x5ab56)
	@   bildet den Listenindex ueber die Tabelle @ vaddr 0x202db8 auf eine
	@   Nachricht ab:  64 65 66 67 69 70 71 72
	@   Die Liste zeigt 8 Eintraege (Modi 0,1,2,3,5,6,7,8 — track_rec = 4 ist
	@   per "128M SCHEME" ausgeblendet), also ist Nachricht = 64 + Modus.
	@   Daraus:  Modus 5 (Foto) -> 69,  Modus 0 (Video) -> 64.
	@
	@ Adressen (vaddr):
	@   FunctionSelectWindow->Close  0x697ac
	@   BottomBarFunctionProc         0x5aeac
	@   PreviewWindow::PostMsg        0x5aa08   (self, arg1, msg, arg3)
	@   system@plt                    0x1c94c   (ARM-Stub, per blx)
	@   Scriptname                    0x2032a2  (32 B, frueher der Log-Format-
	@                                             String von FunctionChangeProc;
	@                                             einziger Zeiger darauf lag in
	@                                             diesem Slot und ist damit frei)
	.syntax unified
	.thumb

	.org 0x5afe0

	.global func_proc
func_proc:
	push	{r4, r5, lr}
	mov	r4, r0			@ r4 = self
	mov	r5, r2			@ r5 = Kachelindex

	cmp	r5, #3
	beq	.Lsetup			@ SETUP: BottomBar schliesst das Fenster selbst

	ldr.w	r0, [r4, #0x114]
	bl	0x697ac			@ FunctionSelectWindow->Close

	cmp	r5, #2
	beq	.Lstream

	movs	r2, #69		@ FOTO  -> Modus 5 (normal_pic)
	cmp	r5, #0
	beq	.Lpost
	movs	r2, #64		@ VIDEO -> Modus 0 (normal_rec)
.Lpost:
	mov	r0, r4
	mov	r1, r4
	movs	r3, #0
	bl	0x5aa08			@ PostMsg(self, self, msg, 0)
	pop	{r4, r5, pc}

.Lsetup:
	mov	r0, r4
	movs	r1, #1
	bl	0x5aeac			@ BottomBarFunctionProc(self, 1)
	pop	{r4, r5, pc}

.Lstream:
	movw	r0, #0x32a2
	movt	r0, #0x0020		@ r0 = 0x002032a2
	blx	0x1c94c			@ system("/mnt/extsd/start_streaming.sh &")
	pop	{r4, r5, pc}

	@ 4-Kachel-Dispatcher v5 — Ersatz fuer PreviewWindow::FunctionChangeProc
	@ vaddr 0x5afe0, Slot 0x5afe0..0x5b030 (80 B)
	@
	@ Signatur wie Original: (r0 = self = PreviewWindow, r1 = ?, r2 = Kachelindex)
	@
	@   0 = FOTO    -> ModeChangeProc(self, 4)   [msg 69 = normal_pic]
	@   1 = VIDEO   -> ModeChangeProc(self, 0)   [msg 64 = normal_rec]
	@   2 = STREAM  -> system("/mnt/extsd/start_streaming.sh &")
	@   3 = SETUP   -> BottomBarFunctionProc(self, 1)
	@
	@ NEU in v5 (v9/v10 haben die Vordertaste nicht zum Ausloesen gebracht):
	@   Statt PostMsg(...) + eigenem Close() wird PreviewWindow::ModeChangeProc
	@   (vaddr 0x5ab54) aufgerufen — genau der Code, den das Stock-Firmware
	@   ausfuehrt, wenn man in der Modusliste "Foto" waehlt. Verifiziert:
	@
	@       5ab54: cmp  r2, #7                 @ Modusindex
	@       5ab56: push {r0, r1, r4, lr}
	@       5ab58: mov  r4, r0
	@       5ab5a: bls  5ab74
	@       5ab74: ldr  r1, [pc, #48]          @ Tabelle 0x202db8
	@       5ab78: ldr.w r2, [r1, r2, lsl #2]  @ msg = table[idx]
	@       5ab7e: bl   5aa08                  @ PostMsg(self, self, msg, 0)
	@       5ab8a: bl   5aa08                  @ PostMsg(self, 0,    201, 0)
	@       5ab8e: ldr.w r0, [r4, #0xec]       @ Modusliste
	@       5ab98: b.w  66de0                  @ Close([self+0xec])
	@
	@   v9/v10 machten nur Schritt 1 und schlossen das Kachelmenue direkt per
	@   0x697ac. Der 201-Broadcast fehlte — deshalb hielt main.cpp das
	@   "function window" weiter fuer aktiv (Log main.cpp:648), und die
	@   OK-/Vordertaste (keyCode 130) loeste nicht aus.
	@
	@ Modustabelle @ vaddr 0x202db8 (int32):
	@       64 65 66 67 69 70 71 72
	@   idx 0 = normal_rec (VIDEO), idx 4 = normal_pic (FOTO)
	@   (mode_track_rec ist per "128M SCHEME" aus der Liste entfernt, daher
	@    rutschen die Foto-Modi auf die Indizes 4..7.)
	@
	@ Adressen (vaddr):
	@   FunctionSelectWindow->Close  0x697ac   (hide + EnableWindow + SetActiveWindow)
	@   PreviewWindow::ModeChangeProc 0x5ab54  (self, modus in r2)
	@   BottomBarFunctionProc         0x5aeac
	@   PreviewWindow::PostMsg        0x5aa08
	@   system@plt                    0x1c94c  (ARM-Stub, per blx)
	@   Scriptname                    0x2032a2 (32 B)
	.syntax unified
	.thumb

	.org 0x5afe0

	.global func_proc
func_proc:
	push	{r4, r5, lr}
	mov	r4, r0			@ r4 = self (PreviewWindow)
	mov	r5, r2			@ r5 = Kachelindex

	cmp	r5, #3
	beq	.Lsetup			@ SETUP: BottomBar schliesst das Fenster selbst

	ldr.w	r0, [r4, #0x114]	@ FunctionSelectWindow
	bl	0x697ac			@ Close()

	cmp	r5, #2
	beq	.Lstream

	movs	r2, #4			@ FOTO  -> idx 4 (msg 69)
	cmp	r5, #0
	beq	.Lpost
	movs	r2, #0			@ VIDEO -> idx 0 (msg 64)
.Lpost:
	mov	r0, r4
	bl	0x5ab54			@ ModeChangeProc(self, modus)
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

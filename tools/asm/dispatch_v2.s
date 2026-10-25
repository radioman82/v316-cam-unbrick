	@ 4-Kachel-Dispatcher (Ersatz fuer FunctionChangeProc, vaddr 0x5afe0)
	@
	@ Signatur wie Original: (r0 = self = PreviewWindow, r1 = ?, r2 = sel)
	@   sel 0 = FOTO     -> ChangeWorkMode(self, 5, 0)   [mode_normal_pic]
	@   sel 1 = VIDEO    -> ChangeWorkMode(self, 0, 0)   [mode_normal_rec]
	@   sel 2 = STREAM   -> system("/mnt/extsd/start_streaming.sh &")
	@   sel 3 = SETUP    -> BottomBarFunctionProc(self, 1)  (bewaehrt)
	@
	@ Wichtig: NICHT mehr PostMsg(59,1) benutzen — 59 ist MSG_BLUETOOTH_ENABLE!
	@
	@ Modusliste (aus zh-DE.xml, string-array "mode_list"):
	@   0 normal_rec  1 slowly_rec  2 loop_rec  3 timelapse_rec  4 track_rec
	@   5 normal_pic  6 auto_pic    7 continue_pic  8 timing_pic
	@
	@ Adressen (vaddr):
	@   ChangeWorkMode           0x6bd68   (self, newMode, force)
	@   BottomBarFunctionProc    0x5aeac   (self, index)
	@   FunctionSelectWindow->Close 0x697ac
	@   system@plt               0x1c94c
	@   Streaming-String         0x2032a2
	.syntax unified
	.thumb

	.org 0x5afe0

	.global func_proc
func_proc:
	push	{r4, r5, lr}
	mov	r4, r0			@ r4 = self (PreviewWindow)
	mov	r5, r2			@ r5 = sel

	cmp	r5, #3
	bne	.Lclose
	@ ---- SETUP: bewaehrter Weg ueber die BottomBar
	mov	r0, r4
	movs	r1, #1
	bl	0x5aeac
	pop	{r4, r5, pc}

.Lclose:
	@ Menue schliessen, damit das Livebild wieder sichtbar wird
	ldr.w	r0, [r4, #0x114]
	bl	0x697ac

	cmp	r5, #2
	bne	.Lmode
	@ ---- STREAM
	ldr	r0, =0x2032a2
	blx	0x1c94c			@ system()
	pop	{r4, r5, pc}

.Lmode:
	movs	r1, #5			@ FOTO  = mode_normal_pic
	cmp	r5, #0
	beq	.Lgo
	movs	r1, #0			@ VIDEO = mode_normal_rec
.Lgo:
	mov	r0, r4
	movs	r2, #0			@ force = 0
	bl	0x6bd68			@ ChangeWorkMode(self, mode, 0)
	pop	{r4, r5, pc}

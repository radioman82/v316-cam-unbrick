	@ 4-Kachel-Dispatcher v4 — Ersatz fuer PreviewWindow::FunctionChangeProc
	@ vaddr 0x5afe0, Slot 0x5afe0..0x5b030 (80 B)
	@
	@ Signatur wie Original: (r0 = self = PreviewWindow, r1 = ?, r2 = Kachelindex)
	@
	@   0 = FOTO    -> PostMsg(self, self, 69, 0)   [Modus 5 = normal_pic]
	@   1 = VIDEO   -> PostMsg(self, self, 64, 0)   [Modus 0 = normal_rec]
	@   2 = STREAM  -> system("/mnt/extsd/start_streaming.sh &")
	@   3 = SETUP   -> BottomBarFunctionProc(self, 1)   (bewaehrt, schliesst selbst)
	@
	@ NEU in v4 (gegen "Vordertaste tut nichts"):
	@   Nach FunctionSelectWindow->Close (0x697ac) wird zusaetzlich
	@   PreviewWindow::Show() aufgerufen (eigener vtable-Slot 0x6c).
	@   Close blendet das Menue nur aus (vtable[0x14](self,0)); es meldet dem
	@   Fenstermanager KEIN neues aktives Fenster. Ergebnis: main.cpp haelt
	@   weiter das "function window" fuer das aktuelle Fenster
	@   (Log: main.cpp:648 "function window can not play key tone"), und die
	@   OK-Taste (keyCode 130 = Ausloeser) wird vom unsichtbaren Menue
	@   geschluckt statt ein Foto zu machen.
	@   Show() setzt das Vorschaufenster wieder als aktives Fenster.
	@   Genau dieser Slot 0x6c wird auch vom Autostart-Show-Stub benutzt
	@   (dort auf [self+0x114], also das Menue) — er funktioniert nachweislich.
	@
	@ Warum PostMsg und nicht ChangeWorkMode direkt:
	@   ChangeWorkMode (0x6bd68) synchron im Tasten-Handler aufzurufen hat in v7
	@   zum Absturz gefuehrt. Die Stock-Firmware arbeitet ausschliesslich ueber
	@   PostMsg (0x5aa08) — die Nachricht wird in die Queue gelegt und erst
	@   nach dem Verlassen des Tasten-Handlers verarbeitet.
	@
	@ Herkunft der Nachrichtennummern:
	@   PreviewWindow::ModeChangeProc (vaddr 0x5ab56) bildet den Listenindex
	@   ueber die int32-Tabelle @ vaddr 0x202db8 auf eine Nachricht ab:
	@       64 65 66 67 69 70 71 72
	@   Die Liste zeigt 8 Eintraege (Modi 0,1,2,3,5,6,7,8 — track_rec = 4 ist
	@   per "128M SCHEME" ausgeblendet), also ist Nachricht = 64 + Modus.
	@   Daraus:  Modus 5 (Foto) -> 69,  Modus 0 (Video) -> 64.
	@
	@ Adressen (vaddr):
	@   FunctionSelectWindow->Close  0x697ac
	@   PreviewWindow::Show          self->vtable[0x6c]
	@   BottomBarFunctionProc         0x5aeac
	@   PreviewWindow::PostMsg        0x5aa08   (self, arg1, msg, arg3)
	@   system@plt                    0x1c94c   (ARM-Stub, per blx)
	@   Scriptname                    0x2032a2  (32 B, frueher der Log-Format-
	@                                             String von FunctionChangeProc)
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

	ldr.w	r0, [r4, #0x114]
	bl	0x697ac			@ FunctionSelectWindow->Close  (nur ausblenden)

	mov	r0, r4
	ldr	r3, [r4]
	ldr	r3, [r3, #0x6c]
	blx	r3			@ PreviewWindow::Show()  -> aktives Fenster

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

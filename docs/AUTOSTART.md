# Autostart: 4-Kachel-Menü beim Booten automatisch anzeigen

**Status: gelöst und auf Hardware verifiziert (Kaltstart).**
Build `sdvcam_4tiles_autostart_v6`, MD5 `7b08a865e4ae7c5dc107e5a4f684e363`

---

## 1. Aufgabe

Die Kamera soll nach dem Einschalten nicht mit dem Livebild starten, sondern
direkt das 4-Kachel-Menü (MODUS / ALBUM / SETUP / ZURÜCK) zeigen. Bisher war
dafür ein Tastendruck auf **Seite UP** nötig — bei defekter Fronttaste die
einzige Möglichkeit, ins Menü zu kommen.

---

## 2. Lösung: zwei Hooks + Einmal-Flag

Der Ansatz ist bewusst zweistufig, weil **kein einzelner Ankerpunkt** beides
gleichzeitig erfüllt: einen gültigen `PreviewWindow*` **und** eine bereits
vollständig geladene Kachel-Ressourcenbasis.

```
Hook 1  @ 0x6c0e8   Ende PreviewWindow::OnWindowLoaded (preview.cpp)
        -> startet system("(sleep 1;>/tmp/A)&")   [nicht blockierend, 0.00 s]
           Der Hintergrund-Job legt das Flag ~1 s später an, also nachdem die
           Kachel-Ressourcen geladen sind (42.913 s) und bevor die
           Boot-Nachrichten abgearbeitet werden (43.910 s).

Hook 2  @ 0x5ca28   Anfang PreviewWindow::HandleMessage (preview_window.cpp)
        -> hier ist r0 = PreviewWindow und [self+0x114] = FunctionSelectWindow*
           Flag prüfen -> Flag löschen (entwaffnen!) -> Show() über den
           vorhandenen Show-Stub @0x1f5130.
```

### Warum nicht direkt in Hook 1 `Show()` rufen

In `OnWindowLoaded` ist `r4` **nicht** das `PreviewWindow`. Der Code dort
verwendet `[r4+0x90]` (WindowManager), `[r4+0x94]` (Work-Mode) und `[r4+0x98]`.
Ein Zugriff auf `[r4+0x114]` liefert einen Nicht-NULL-Zeiger auf Müll —
Autostart v2 ist daran mit `PC: 0x1f5166` (SIGABRT) gestorben.

### Warum nicht der `MSG_MODE_SWITCH_DONE`-Handler

`0x5caee` ist zu früh: dort sind die Kachel-Ressourcen noch nicht geladen,
`Show()` stürzt bei `0x56d32` ab.

### Warum das Flag erst löschen, dann `Show()` rufen

`Show()` kann selbst Nachrichten erzeugen, die wieder in `HandleMessage`
laufen. Ohne Entwaffnen vor dem Aufruf gäbe es eine Rekursion.

---

## 3. Zeitachse (gemessen aus `/tmp/log/sdvcam.INFO`)

| Zeit | Ereignis |
|------|----------|
| 42.575 | `PreviewWindow`-Konstruktor |
| 42.600 | `OnWindowLoaded` #1 (`preview.cpp:147`) |
| 42.913 | Kachel-Ressourcen geladen (`function_select_window.cpp:129`) — **ab hier ist `Show()` sicher** |
| 43.055 | `OnWindowLoaded` #2 → `preview.cpp:155 current work mode[0]` |
| 43.910 | `HandleMessage`: Flush der Boot-Nachrichten (`MSG_NOT_SUPPORT_EIS` …) |
| 120.000 | nächste Nachricht (`MSG_AUTO_SCREENSAVE`) |

Der 1-s-Verzug im Hintergrund-Job trifft genau das Fenster zwischen 42.913 und
43.910. Wird `HandleMessage` in diesem Fenster nicht erreicht, bleibt das Flag
einfach stehen und der nächste Aufruf (120 s) greift — kein Fehlerfall.

---

## 4. Speicherlayout / Code-Cave

Die Code-Cave ist der Engpass: **104 freie Bytes** in `.rodata`.

```
0x1f5130 .. 0x1f5139   Show-Stub (10 B, bereits vorhanden, unverändert)
0x1f513c .. 0x1f51a3   Autostart-Stub (104 B, 0 B Reserve)
0x1f51a4               echte Strings beginnen ("RemoveFile", "IsMounted", …)
```

Der Stub passt exakt — jede Änderung an den Strings sprengt ihn. Deshalb:

* Alle Strings in **einem** 4-Byte-ausgerichteten Block, damit `adr`
  (imm8×4, 2 Byte) statt `addw` (4 Byte) reicht.
* `"/tmp/A"` wird **nicht** doppelt gespeichert, sondern als eigener
  `.asciz`-Eintrag zwischen den Befehlen platziert.
* `>` statt `mkdir` für das Flag: idempotent (kein rc=1 beim zweiten Lauf)
  und 5 Byte kürzer.

> **Wichtig:** Große Null-Läufe in `.rodata` (z. B. 272 B bei `0x2260f4`) sind
> **keine** nutzbaren Caves — dort liegen echte numerische Datenarrays.

---

## 5. Der Stub

```asm
	.syntax unified
	.thumb

	.org 0x5ca28
	b.w	hook2			@ Hook 2: HandleMessage-Anfang

	.org 0x6c0e8
	b.w	hook1			@ Hook 1: OnWindowLoaded-Ende

	.org 0x1f513c
hook1:
	adr	r0, cmd_bg
	blx	0x1c94c			@ system("(sleep 1;>/tmp/A)&")
	ldr	r0, [r4, #144]		@ Originalbefehl von 0x6c0e8
	b.w	0x6c0ec			@ Rest des Original-Epilogs

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
	push.w	{r4, r5, r6, r7, r8, r9, r10, r11, lr}	@ Original-Prolog
	b.w	0x5ca2c

	.align 2
cmd_rm:
	.asciz	"rm -f /tmp/A"
	.align 2
path_flag:
	.asciz	"/tmp/A"
	.align 2
cmd_bg:
	.asciz	"(sleep 1;>/tmp/A)&"
```

---

## 6. Patches im Gesamtbuild

Basis: `sdvcam_4tiles_final` (MD5 `5ce4e6c6f7125394b099dae940f124ed`)

| # | Vaddr | Datei-Offset | Länge | Inhalt |
|---|-------|--------------|-------|--------|
| B | 0x59852 | 0x49852 | 1 | `tbb`-Eintrag 2: `0x15` → `0x0b` |
| C | 0x5afe0 | 0x4afe0 | 76 | 4-Kachel-Dispatcher |
| D | 0x5ba46 | 0x4ba46 | 4 | `b.w 0x1f5130` (Show-Stub) |
| Show | 0x1f5130 | 0x1e5130 | 10 | `ldr.w r0,[r0,#0x114]; ldr r3,[r0]; ldr r3,[r3,#108]; bx r3` |
| Stream | 0x1f32a2 | 0x1f32a2 | 32 | `/mnt/extsd/start_streaming.sh &\0` |
| **F** | **0x6c0e8** | **0x5c0e8** | **4** | **`b.w 0x1f513c` (Hook 1)** |
| **G** | **0x5ca28** | **0x4ca28** | **4** | **`b.w hook2` (Hook 2)** |
| **Stub** | **0x1f513c** | **0x1e513c** | **104** | **Autostart-Stub** |

---

## 7. Verifikation (wichtig!)

**Ein Log-Eintrag beweist nichts.** Zeilen wie
`function_select_window.cpp:129 <LoadIconViewResource>` erscheinen bei
**jedem** Boot — das ist normales Vorladen der Kachel-Ressourcen, nicht das
Anzeigen des Menüs.

Zwei brauchbare Verfahren:

### 7.1 Statik-Test (schnell)
```sh
dd if=/dev/fb0 bs=1280 count=480 2>/dev/null | md5sum   # 3x im Abstand von 2 s
```
Drei identische Hashes → der Schirm ist statisch (Menü steht).
Ändert sich der Hash, läuft eine Live-Vorschau.

### 7.2 ASCII-Abbild des Framebuffers (visueller Beweis)
`tools/fbgrab.py` liest `/dev/fb0` (320×480, 32 bpp, stride 1280) zeilenweise,
sampelt jedes 8. Pixel und überträgt nur ~1,2 KB über die serielle Konsole.
Ergebnis nach dem Fix:

```
+----------------------------------------+
|========================================|
|%...................=...................|
|%.......@@@@@.......=.......:::.........|   <- Kachel 1      | Kachel 2
|%.......:@@::.......=.......:::::.......|
|%...................=...................|
|%.....@....@@@-.....=....  .@*..=.......|
|%...................=...................|
|%...................=...................|
| .=================.=...................|   <- Trennlinie y≈128
| ...................=...................|
| .........==........=........:.:........|
| .........=.........=.........:.........|   <- Kachel 3      | Kachel 4
| ...................=...................|
| ...@..@...=@..@@...=..... .@ @@.@@.....|
| ....-.**.:..*.+....=......+....**......|
|                                        |
|             (unterer Bereich leer)     |
+----------------------------------------+
```

Die vertikale Trennlinie exakt bei Spalte 20 (= x 160) und der horizontale
Trenner bei y ≈ 128 entsprechen `item_width=160`, `item_height=120` aus
`function_select_window.cpp:141` — also einem 2×2-Raster.

Referenzwerte:
* Livebild-Baseline (nur Vorschau): `00f0acd6f5387269b66d4d74eb10a3a6`
* Menü (v6): `882fff0d930173964f5fab73ca2627ce`

---

## 8. Verworfene Ansätze (und warum)

| Versuch | Ansatz | Ergebnis |
|---------|--------|----------|
| v1 | `MSG_MODE_SWITCH_DONE`-Handler (`0x5caee`) | Crash bei `0x56d32` — zu früh |
| v2 | `Show()` direkt am Ende von `OnWindowLoaded`, `[r4+0x114]` | Crash bei `0x1f5166` — `r4` ist nicht `PreviewWindow` |
| Probe | Nur `cbz` auf `[r4+0x114]` | **Falsch-positiv** (`/tmp/OL_OK`): Zeiger war nicht NULL, aber Müll |
| v3 | `[[r4+0x90]+0x114]` | kein Crash, aber `Show()` still übersprungen — `[r4+0x90]` ist der WindowManager |
| v4 | zwei Hooks, gefiltert über Work-Mode ≤ 7 | Crash bei `0x1f5136` — Hook feuerte in `OnWindowLoaded` #1, Vtables noch nicht bereit |
| v5 | zwei Hooks mit Hintergrund-Flag | Flag wurde nie konsumiert: String war `"/tmp/A)&"` (falsch), `access()` schlug fehl |
| **v6** | **zwei Hooks, Strings korrigiert, 1 s Verzug** | **funktioniert** |

**Lehre:** Ein Probe-Build, der nur auf NULL testet, ist wertlos. Immer den
Wert selbst prüfen (z. B. per `system("echo … >> /tmp/probe")`).

---

## 9. Wichtige Adressen

| Sache | Wert |
|-------|------|
| Adressregel R-Segment | `vaddr = datei_offset + 0x10000` |
| Adressregel RW-Segment | `vaddr = datei_offset + 0x20000` |
| `system@plt` | `0x1c94c` (ARM-Stub, mit `blx` aufrufen) |
| `access@plt` | `0x1cc3c` |
| `PreviewWindow::HandleMessage` | `0x5ca28` (`push.w {r4-r11,lr}`, dann `mov r6,r3`) |
| `PreviewWindow::OnWindowLoaded` | `0x6c018`, Hook am Ende `0x6c0e8` |
| `FunctionSelectWindow::Show()` | Vtable-Slot 108 |
| Show-Stub | `0x1f5130` (10 B) |

> `objdump` **ohne** `--adjust-vma` verwenden — mit dem Schalter verschiebt
> sich alles um +0x10000.

---

## 10. Deployment

```sh
python tools/patch_autostart.py sdvcam_4tiles_final sdvcam_4tiles_autostart_v6
# -> MD5 7b08a865e4ae7c5dc107e5a4f684e363
```

Auf die Kamera: `tools/apply_build.py` (schreibt nur die geänderten Regionen
per `printf | dd … conv=notrunc`, verifiziert die MD5 und startet die App neu).

Persistenz: `/etc/init.d/S01app` bind-mountet `/mnt/extsd/sdvcam` nach
`/usr/bin/sdvcam` — der Build auf der SD-Karte überlebt Stromausfall.

---

## 11. Getestet

- [x] App-Neustart (`killall sdvcam` + Neustart): Menü erscheint
- [x] **Kaltstart (`reboot`)**: Menü erscheint ohne Tastendruck
- [x] Sichtprüfung am Gerät: ~1 s Vorschaubild, dann klappt das 4-Kachel-Menü auf
- [x] `/usr/bin/sdvcam` MD5 == v6 nach Kaltstart
- [x] Flag `/tmp/A` wird konsumiert
- [x] kein Crash, Prozess läuft stabil
- [ ] Rückweg aus dem Menü ins Livebild (Taste ZURÜCK) — Feldtest offen
- [ ] `start_streaming.sh` für Kachel STREAM — Feldtest offen

---

## 12. Betriebs-Fallstrick: U-Boot-Autoboot wird durch serielle Daten abgebrochen

**Symptom:** Bildschirm bleibt schwarz, die Konsole antwortet nur noch mit
`sunxi#` und führt keine Befehle aus.

**Ursache:** Die Kamera war neu gestartet (Watchdog / Stromglitch). Während der
Autoboot-Wartezeit von U-Boot bricht **jedes eintreffende Byte** den Autoboot
ab. Schickt man in diesem Moment ein Kommando über COM11, bleibt die Kamera im
U-Boot-Prompt hängen — der Kernel wird nie geladen, also bleibt das Display
schwarz. Das ist **kein** Fehler des Autostart-Patches.

**Rettung:** Im U-Boot-Prompt `reset` senden (funktioniert auch ohne Echo):

```
reset
-> resetting ...
   [146]HELLO! BOOT0 is starting!
```

**Regel für die Werkzeuge:** Nach einem Neustart einige Sekunden **nichts**
senden, nur passiv mitlesen. `tools/fbgrab.py` prüft deshalb zuerst den
Prompt-Zustand — bei `sunxi#` sofort abbrechen statt blind zu schreiben.

**Nebenbefund:** Beim Kaltstart meldet der Kernel
`FAT-fs (mmcblk0): Volume was not properly unmounted` — Folge der harten
`reboot`-Aufrufe. Unkritisch, aber vor einem Feldeinsatz `fsck` laufen lassen.

---

## 13. „Kamera geht nach kurzer Zeit aus" = Bildschirmschoner

**Symptom:** Nach dem Boot erscheint das Menü, kurze Zeit später wird das
Display schwarz. Die Kamera wirkt ausgeschaltet.

**Es ist kein Power-Off.** Nachweis über `/proc/uptime`: die Laufzeit steigt
weiter, der Prozess `sdvcam` lebt, das Log wächst nicht mehr. Es wird nur das
**Panel** abgeschaltet.

**Ursache:** `ml_camera_autoscreensaver = 3`. Die Optionsliste
(`zh-DE.xml`, `string-array ml_camera_autoscreensaver`):

| Wert | Bedeutung |
|------|-----------|
| 0 | Ausschalten (aus) |
| 1 | 30 S |
| 2 | 1 Min |
| 3 | 2 Min |

Der Log bestätigt es exakt: `power_manager.cpp:790 <AutoScreenSaveTimerProc>
allow screen save` bei **+120,0 s** nach App-Start.

Auto-Shutdown ist **nicht** die Ursache:
* `device_setting.cpp:98 <InitAutoShutDown>the function of auto shut down is close`
* `ml_camera_timedshutdown = 0`, `ml_device_standby = 0`

**Wo der Wert liegt:**
* `/data/setting.lua` — persistent (Overlay auf jffs2)
* `/tmp/data/setting.lua` — Arbeitskopie (tmpfs)
* `/usr/share/app/sdv/setting.lua` — Default, dort steht bereits `0`

**Abschalten:** `python set_screensaver.py 0` (sichert vorher nach
`/mnt/extsd/setting.lua.bak` und schreibt beide Dateien).

**Verifikation:** Nach dem Neustart darf im Log **kein** `ScreenSave`-Eintrag
mehr auftauchen. Getestet bis +145 s: 0 Treffer, Menü unverändert sichtbar.

> Ohne Fronttaste ist ein aktivierter Screensaver besonders ärgerlich: es gibt
> keine Möglichkeit, das Display wieder zu wecken.

---

## 14. Nebenbefund: Selbsttest der App schlägt fehl

`utils.cpp:157 <verify_bin_md5>md5 check failed` — die App vergleicht sich mit
`/data/app_md5` (dort `f9271ddd…`, unser Build `7b08a865…`). Das ist nur eine
Warnung, der Start läuft normal weiter. Bei Bedarf kann `/data/app_md5` auf die
eigene MD5 gesetzt werden, damit das Log sauber bleibt.



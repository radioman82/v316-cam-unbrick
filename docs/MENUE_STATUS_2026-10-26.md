# Menü & Tastatur — Gesamtstand 26.10.2026

Statusbericht zum Umbau des Vorabmenüs der Allwinner V316 Cam (Allwinner V316).
Alles hier Beschriebene ist auf dem Gerät erprobt, sofern nicht ausdrücklich als
Vermutung gekennzeichnet.

---

## 1. Kurzfassung

| Thema | Stand |
|---|---|
| Vordertaste (PWRON) repariert | **erledigt**, funktioniert (Foto/Video-Umschaltung, Aus/Ein) |
| Akkubetrieb | **erledigt**, Kamera läuft ohne USB |
| Vorabmenü nach dem Start | **funktioniert** — Einstellungsfenster mit Modus / Gerät / Zurück |
| Seitentaste holt Menü aus der Vorschau | **funktioniert** (Variante 6) — aber nur eine der beiden Tasten sauber |
| Modus-Auswahl auf der Seitentaste | **funktioniert** (Variante 9) — kein Absturz mehr |
| Lade-/Massenspeicher-Dialog weg | **funktioniert** (Variante 6 + 9) |
| 4-Kachel-Menü (Foto/Video/Stream/Setup) | **endgültig nicht reanimierbar** — toter Code, wirft eine C++-Ausnahme |
| Absturz bei Seitentaste im Vorschaubild | **behoben und auf dem Gerät verifiziert** |

**Aktuell auf der Kamera:** `menu9` (MD5 `34d80376efd31fed7faa7dbcb842b6db`).

Damit startet die Kamera im Einstellungsmenü, und ein Druck auf die Seitentaste im
Vorschaubild öffnet die Modus-Auswahl, statt die App zu beenden.

---

## 2. Gerät und Firmware (belegte Fakten)

| Sache | Wert |
|---|---|
| SoC | Allwinner `sun8iw16` / V316 (`allwinner,sun8iw16p1`) |
| Kernel | `Linux 4.9.118 (dv002@fjj) #1 SMP PREEMPT Mon Jun 24 18:36:39 CST 2019` |
| Userspace | armv7l, MiniGUI-Processes, BusyBox |
| App | `/usr/bin/sdvcam`, 3.407.624 Bytes, Build-Pfad `/home/dv002/workspace/v316/...` |
| RAM | 45 MB (`MemTotal 46628 kB`) — wichtig, siehe Bildaufnahme |
| Rootfs | squashfs (mtd2, schreibgeschützt) + overlayfs, Upper = mtd3 jffs2, **nur 512 KB** |
| Partitionen | uboot 1M · boot 3M · rootfs 10.5M · overlay 512K · env 128K · bootlogo 384K · UDISK 512K |
| SD-Karte | `/dev/mmcblk0`, FAT, 30 GB |

**Konsequenz aus der Overlay-Größe:** Skripte in `/etc/init.d/` lassen sich
dauerhaft ändern (wenige KB). Die 3,4-MB-Binary passt dort **nicht** — sie muss
von der SD-Karte kommen.

**Zwei verschiedene „Originale“** (wichtig, um Verwirrung zu vermeiden):

| Datei | MD5 | Rolle |
|---|---|---|
| `/usr/bin/sdvcam` im squashfs | `d07814c0e9ad1081a1c234c930194b08` | das echte Werksbinary |
| `sdvcam_v8` (Referenz im Repo) | `ee7425e348fc3d35d09ff62fc405860a` | Arbeitsreferenz, gegen die alle Patches gerechnet sind |

Beide sind 3.407.624 Bytes groß und verhalten sich gleich; die Patches in diesem
Dokument beziehen sich **auf `sdvcam_v8`**.

---

## 3. Wie die Änderungen aufs Gerät kommen (kein Flash-Schreibzugriff)

`/etc/init.d/S00zsdvcam` (720 Bytes, liegt im beschreibbaren Overlay) läuft
zwischen `S00part` und `S01app`:

```sh
P=/mnt/extsd/.sdvcam_patched
if [ ! -f "$P" ]; then
    mount -t vfat -o errors=continue /dev/mmcblk0 /mnt/extsd
fi
if [ -f "$P" ]; then
    mount --bind "$P" /usr/bin/sdvcam
fi
```

Damit gilt:

- Die Kamera bootet **immer** ein sauberes Werkssystem, wenn die SD-Karte fehlt
  oder `.sdvcam_patched` nicht existiert.
- Kein Schreiben in `boot`, `rootfs` oder `uboot`. Rückbau = Datei löschen.
- Prüflog: `/tmp/sdvcam_patch.log` (enthält `bind rc=0` und die MD5).

### Zwei Fallen, die Zeit gekostet haben

1. **`mount -t vfat` ohne `-o errors=continue`** schaltet die Karte nach einem
   Lesefehler still auf `remount-ro` — dann schlägt jeder weitere Schreibvorgang
   fehl, ohne sichtbare Meldung. Der Hersteller benutzt `errors=continue`.
2. **`cp` auf `.sdvcam_patched` erzeugt einen neuen Inode.** Der Bind-Mount hält
   aber den alten Inode — die Datei sieht neu aus, die Kamera läuft weiter das
   alte Binary. Richtig ist ein Überschreiben **in place**:
   ```sh
   cat /mnt/extsd/dbg/sdvcam_menu9.bin > /mnt/extsd/.sdvcam_patched
   ```
   Danach `md5sum /usr/bin/sdvcam` prüfen (muss die neue Summe zeigen), sonst
   `umount /usr/bin/sdvcam` und neu binden.

---

## 4. Tastatur: was die Hardware tatsächlich liefert

Alle Tasten sind **analog** ausgelesen, keine GPIO-Matrix:

| evdev | Treiber | Kernel-Code | App-Code | Taste |
|---|---|---|---|---|
| `event0` | `sunxi-gpadc0` (LRADC) | 115 / 114 / 139 | 135 / — / — | Seitentaste hoch / runter / Menü |
| `event1` | `axp22x-powerkey` (PMIC PWRON) | 116 | 130 | Vordertaste |
| `event2` | `gpiokey` | 107 | — | (unbenutzt) |
| `event3` | `sunchip-gpioirkey` | 60/61/62 | — | IR-Empfänger |

Messungen (Rohdaten auf SD mitgeschnitten, `tools/keys.py`):

- **Kein Prellen.** Jeder Druck erzeugt genau ein `down` und ein `up`.
- Haltezeiten streuen stark: Seite 40–425 ms, Vorder 57–409 ms.
- Bei mehr als ~250 ms schickt der Treiber `value=2` (Autorepeat).

Die ADC-Seitentasten waren bei 8 von 8 Drücken sauber. Der PMIC-Zweig der
Vordertaste war zeitweise **komplett stumm** (kein evdev-Event, Zähler in
`/proc/interrupts` für `axp22x` stieg nicht) — das war der Hardwaredefekt, der
durch Nachlöten/Reinigen behoben wurde. Seitdem funktioniert die Taste.

---

## 5. Der Long-Press-Konflikt (erklärt „unzuverlässige“ Tasten)

Die App unterscheidet **kurz** und **lang** auf derselben Taste 130:

```
0x5b9c6  cmp r5,#130
0x5b9c8  beq 0x5ba4a          ; Handler
...
0x5ba4a:  r6 (inLongPress) == 1  ->  system("poweroff -f")
          r6 == 0               ->  CloseTopWindow() -> ggf. Auslöser
```

`inLongPress` kommt aus `__mg_key_longpress_time`. Die App setzt den Wert selbst
in ihrer Init-Funktion:

```
0x4e9b8: ldr r3,[pc]      ; -> 0x35f9c0 = &__mg_key_longpress_time
0x4e9ba: movs r2,#100     ; 100 ms (!)
0x4e9bc: str r2,[r3,#0]
```

Gleichzeitig verlangt der PMIC hardwaremäßig **1000 ms** Halten zum Einschalten
(Device Tree `pmu_powkey_on_time = 1000`, `pmu_powkey_off_time = 6000`).

**Daraus folgt:** Es gibt keine Haltedauer, die einschaltet, aber nicht
ausschaltet — jeder Druck, der lang genug zum Einschalten ist, liegt über der
100-ms-Ausschaltschwelle. Das erklärt „ich kann nicht ein-/ausschalten“ **ohne**
Hardwaredefekt.

**Praktischer Umgang:** Schwelle zur Laufzeit auf 700 ms setzen
(`tools/set_thresh.py 700`, schreibt 4 Bytes nach `/proc/<pid>/mem`). Dann gilt:
Tipp = Tipp, 0,7–6 s = Software-Aus, > 6 s = PMIC-Hartaus. Der Wert geht bei
jedem Reboot verloren, weil die App ihn neu auf 100 setzt.

---

## 6. Fensterarchitektur (die Grundlage für alles Weitere)

`WindowManager::Init(startId)` @ `0x62980` legt die Fenster an:

| ID | Klasse | Größe | ctor |
|---|---|---|---|
| 1 | **SettingWindow** | 520 | `0x64e28` |
| 2 | PreviewWindow | 408 | `0x5c6fc` |
| 3 | PlaybackWindow | 332 | `0x5f988` |
| 4 | StatusBarWindow | 372 | `0x60424` |
| 5 | UsbModeWindow | 228 | `0x619b8` |
| 6 | ScreenSave/Lock | 372 | `0x689d8` |
| 7 | BootGuideWindow | 260 | `0x6a018` |

Fensterwechsel: `ChangeWindow(oldId, newId, flag, r3)` @ `0x6264c` —
`newId>0` → `Show()`, `oldId>0` → `Hide()`.

Das **PreviewWindow ist der Koordinator** und erzeugt seine Unterfenster selbst:

| Offset | Klasse | ctor | vtable |
|---|---|---|---|
| `+0xec` | ModelSelectWindow | `0x67654` | `0x205fd0` |
| `+0xf0` | (weiteres Fenster) | `0x597e8` | — |
| `+0x114` | **FunctionSelectWindow** (4-Kachel-Menü) | `0x69de8` | `0x20679c` |
| `+0x118` | (weiteres Fenster) | `0x58b90` | — |

Gemeinsame Basis-API (vtable): `+0x10` IsVisible · `+0x18` Show · `+0x1c` Hide ·
`+0x6c` show/activate · `+0x74` GetChildByName.

**Startfenster** ist eine einzige Konstante in der Init-Funktion:

```
0x4e9c4: movs r1,#2        ; startId = 2 (PreviewWindow)
0x4e9c6: bl 0x62574        ; GetWindowById(2) -> PreviewWindow wird angelegt
0x4e9d4: bl 0x62980        ; WindowManager::Init(2)
```

---

## 7. Das Vorabmenü: was funktioniert

**Lösung = Startfenster auf 1 (SettingWindow) + eine Seitentaste.**

Das SettingWindow ist inhaltlich bereits das gesuchte Auswahlmenü — es hat drei
Kacheln und eine Liste:

| Element | Position/Größe | Bedeutung |
|---|---|---|
| `mode_gview` | 0,0 · 66×80 | **Modus** (Video / Foto / Wiedergabe) |
| `device_gview` | 0,80 · 66×80 | **Gerät** (Einstellungen) |
| `return_gview` | 0,160 · 66×80 | **Zurück** (in die Vorschau) |
| `listtable` | 66,0 · 254×240 | Liste der Einträge rechts |

Damit ist die Bedienung genau wie gewünscht: mit den Pfeiltasten (Seitentasten)
durch die Kacheln und die Liste, mit der oberen OK-/Vordertaste auswählen.

**Zwei Patchstellen waren nötig** (die erste allein wirkt nicht!):

| Offset | alt → neu | Wirkung |
|---|---|---|
| 256460 | `02` → `01` | `Init(2)` → `Init(1)`: Start im Einstellungsmenü |
| 338356 | `19 46` → `00 21` | `Init` versteckt Fenster 1 nicht mehr |

**Warum die zweite Stelle nötig ist:** `Init(startId)` ruft intern
`ChangeWindow(oldId=1, newId=startId, 1)` auf — `oldId` ist hart auf 1 verdrahtet.
Mit `startId=1` wird Fenster 1 also **gezeigt und sofort wieder versteckt**. Der
Patch ersetzt `mov r1,r3` durch `movs r1,#0`, damit das Verstecken unterbleibt.

Zusätzlich (unabhängig davon): **USB-Dialog abschalten**, Offset 334572
`98 47` → `00 bf` — das ist der `Show`-Aufruf in `UsbModeWindow::HandleMessage`
(`0x61aec`). Nur die Sichtbarkeit fällt weg, Log und Zustand bleiben intakt.

---

## 8. Das 4-Kachel-Menü: warum es nicht zurückkommt

Das ursprüngliche Menü (Foto / Video / Streaming / Setup) ist
`FunctionSelectWindow` mit `ShowFunctionSelect()` @ `0x5b030`.

**Befund 1 — es ist toter Code.** Der einzige Aufrufer sitzt bei `0x5ba68` und ist
**unerreichbar**: kein Sprung, kein Jump-Table-Ziel, kein Zeiger auf `0x5b030`
im gesamten Image. Das Fenster wird im Konstruktor des PreviewWindow trotzdem
angelegt — deshalb erscheinen `function_mode.png`, `function_media.png`,
`function_setting.png`, `function_return.png` beim Boot im Log, ohne dass je ein
Fenster aufgeht. Der Hersteller hat den Pfad stillgelegt.

**Befund 2 — es ist auch defekt.** Erzwungen habe ich es trotzdem (Taste 135 auf
`b.w 0x5b030` umgebogen). Ergebnis: **`SIGABRT`**, also eine nicht abgefangene
C++-Ausnahme, geworfen **bevor** der Show-Aufruf erreicht wird:

```
0x3432a  <- 0x345fa  <- 0x501e8  <- 0x1fe60 (__libc_start_main)
```

Ein Zwischenversuch, über einen Trampolin `ChangeWindow(0, 0x114, 1)` das
Unterfenster direkt zu zeigen, beruhte auf einer **Desynchronisation des
Disassemblers** bei `0x69f15` (dort stehen keine gültigen Instruktionen) und
wurde deshalb verworfen, ohne ihn zu testen.

**Ergebnis: Das 4-Kachel-Menü lässt sich nicht wiederherstellen.** Es wäre ein
Debugger auf dem Gerät nötig, um die Ausnahmequelle zu finden — die Kamera hat
kein `gdb`, keinen Symboltisch und nur 45 MB RAM. Aufwand und Risiko stehen in
keinem Verhältnis, zumal das SettingWindow dieselbe Funktion bereits abdeckt.

---

## 9. Der Absturz bei der Seitentaste im Vorschaubild

**Symptom (vom Nutzer):** Nach dem Start kommt das Einstellungsmenü, Navigation
mit den Seitentasten geht, mit der Vordertaste kommt man in die Vorschau zurück —
und ein Druck auf die Seitentaste **stürzt die App ab**.

**Beleg aus dem App-Log** (`/tmp/log/sdvcam.INFO`):

```
preview_window.cpp:147 <keyProc> ------>keyCode = 136 , inLongPress = 0
preview_window.cpp:179 <keyProc> [xl]: do ota update [0]
*** Aborted ... PC: @ 0x5bbfc
*** SIGILL (@0x5bbfc) received ... stack trace:
    @ 0xb6a4c040
    @    0x5bbfc
    @    0x57570
```

**Ursache: mein Patch saß an der falschen Stelle.** Die Tastenverteilung in
`PreviewWindow::keyProc` @ `0x5b83c` ist:

```
0x5b9c6  cmp r5,#130  ->  0x5ba4a   Vordertaste
0x5b9ce  cmp r5,#135  ->  0x5bbf0   Seitentaste A
0x5b9d4  cmp r5,#136  ->  0x5bc50   Seitentaste B
0x5b9da  cmp r5,#132
```

Der Handler für 136 endet bei `0x5bc5c` mit `b.n 0x5bbfc` — er springt also
**mitten in den gemeinsamen Log-Aufruf** des 135-Handlers. `0x5bbfc` ist damit ein
legitimes Sprungziel und **kein** Funktionsanfang.

Der alte 18-Byte-Patch lag auf `0x5bbf0…0x5bc01` und überschrieb genau diese
Einsprungstelle mit den Bytes `fe f7 7b fd`. Taste 136 landete dadurch auf dem
zweiten Halbwort eines `BL` → **`SIGILL` bei `0x5bbfc`**. Das erklärt exakt das
beobachtete Verhalten und auch, warum es nur nach dem Verlassen über die
Vordertaste auftrat: nur dort ist die Vorschau wirklich aktiv und bekommt die
Tasten.

**Der Fix (Variante 9): nur 4 Bytes, an der richtigen Stelle.**

```
310286 (vaddr 0x5bc0e)
   alt:  fe f7 fb fe      bl 0x5aa08    ; PostMsg(self,self,85,...)
   neu:  fe f7 71 fd      bl 0x5a6f4    ; ShowModeSelectWindow(self)
```

Warum das sauber ist:

- Bei `0x5bc08` steht `mov r0,r4` — `r0` enthält dort also bereits `this`
  (das PreviewWindow). Genau das erwartet `ShowModeSelectWindow`.
- Beide Seitentasten (135 **und** 136) laufen durch `0x5bc0e`.
- `0x5bbf0…0x5bc0c` bleibt **unverändert**, das Sprungziel `0x5bbfc` bleibt intakt.
- Nach dem Aufruf läuft der Original-Epilog weiter
  (`add sp,#20` / `pop {r4-r7,pc}`), der Stack bleibt ausgeglichen.

**Verifikation der Kodierung:** Der Encoder (`tools/thumb.py`) reproduziert für
das Originalziel `0x5aa08` exakt die Werksbytes `fe f7 fb fe` — die Rechnung ist
damit gegen echten Code geprüft, nicht nur gegen sich selbst.

**Verifikation am Gerät (26.10.2026):** Nach dem Aufspielen von `menu9` und
Drücken der Seitentaste im Vorschaubild steht im App-Log:

```
preview_window.cpp:147 <keyProc> ------>keyCode = 135 , inLongPress = 0
preview_window.cpp:1586 <ShowModeSelect>show mode select window
```

Keine `SIG`-Zeile, der Prozess läuft weiter, die Modus-Auswahl erscheint auf dem
Display. Der Absturz ist damit behoben.

---

## 10. Alle Patchstellen im Überblick

Basis immer `sdvcam_v8` (`ee7425e3…`), Adressregel `vaddr = datei_offset + 0x10000`.

| Datei-Offset | vaddr | alt → neu | Wirkung |
|---|---|---|---|
| 256460 | `0x3e9cc` | `02` → `01` | Start im Einstellungsmenü |
| 338356 | `0x529b4` | `19 46` → `00 21` | Init versteckt Fenster 1 nicht |
| 334572 | `0x51aec` | `98 47` → `00 bf` | USB-Dialog nicht anzeigen |
| **310286** | **`0x5bc0e`** | `fe f7 fb fe` → `fe f7 71 fd` | **Seitentaste → Modus-Auswahl** |
| ~~310256~~ | ~~`0x5bbf0`~~ | ~~18 Bytes~~ | **verworfen — verursacht SIGILL** |

| Variante | MD5 | Bewertung |
|---|---|---|
| `menu6` | `a3cf2aac60512d3d6d2089535b8d11a3` | auf dem Gerät; Start im Menü ok, **Seitentaste stürzt ab** |
| `menu8` | `af784f70163011bed41f93af80ed3843` | falscher `this` (SettingWindow statt Preview) — **verworfen** |
| `menu9` | `34d80376efd31fed7faa7dbcb842b6db` | **korrigiert, noch nicht aufgespielt** |

**Hinweis zur Basis:** `menu6` wurde noch auf dem echten Werksbinary
(`d07814c0…`) gebaut, `menu9` auf der Arbeitsreferenz `sdvcam_v8` (`ee7425e3…`).
Die drei gemeinsamen Patchstellen liegen in beiden Dateien an derselben Stelle
und haben dieselben Originalbytes — die Binaries unterscheiden sich nur
außerhalb dieser Bereiche. `menu6` liegt deshalb **nur auf der SD-Karte**
(`/mnt/extsd/dbg/sdvcam_menu6.bin`); im Repo ist es nicht enthalten, weil es
sich aus `sdvcam_v8` nicht byte-identisch nachbauen lässt.

---

## 11. Was ich nicht gefunden habe (offene Punkte)

1. **Warum die C++-Ausnahme im 4-Kachel-Pfad fliegt.** Die Ausnahme entsteht vor
   `0x5b076`; ohne Debugger und ohne Symboltisch ist die Quelle nicht
   bestimmbar. Ich habe die Verfolgung bewusst abgebrochen.
2. **Was `PostMsg(85)` eigentlich tut.** Beide Seitentasten senden diese Nachricht
   im Vorschaubild; in Modus 0 ist sie nachweislich wirkungslos. Ob sie in
   anderen Modi etwas auslöst (das Log deutet mit „do ota update“ auf einen
   OTA-Zweig), ist **ungeklärt**. Variante 9 ersetzt den Aufruf — sollte sich
   zeigen, dass 85 in einem Modus wichtig ist, muss man stattdessen den
   85-Handler patchen.
3. **Ob die Modus-Auswahl aus der Taste heraus korrekt *anzeigt*.** Inzwischen
   **belegt** (siehe Abschnitt 9): Die Auswahl erscheint, kein Absturz. Offen ist
   nur noch der komplette Durchlauf — Modus wählen, mit der Vordertaste
   bestätigen, zurück in die Vorschau, auslösen.
4. **Ob die zweite Seitentaste in allen Modi als 136 ankommt.** In der Vorschau
   ja (Log belegt), im Einstellungsmenü navigieren beide Tasten — die genaue
   Zuordnung dort habe ich nicht gemessen.
5. **Die Namenstabelle der Nachrichten ist unbrauchbar.** `MSG`-Tabelle @
   `0x27e870` (183 Zeiger) wird von keinem Code referenziert; die Indizes passen
   nicht zum Code-Enum (msg 81 ist dort „ALARM“, im Code aber der Auslöser). Für
   Patches daher **nie** über Namen argumentieren, nur über Adressen.
6. **Wann `MSG_USB_HOST_CONNECTED` wirklich feuert.** Nicht bei jedem Einstecken;
   nach einem App-Neustart mit steckendem Kabel kam es null Mal. Das Fehlen der
   Log-Zeile ist deshalb kein Beweis, dass der Pfad nicht lief.
7. **Ein Titel „Setup“ im Fenster selbst.** Die Kachelbeschriftung des
   SettingWindow kommt aus den Sprachressourcen (`ml_setting_first_col` u. ä.);
   die Bezeichnung „Setup“ aus dem alten 4-Kachel-Menü steckt in
   `function_setting.png` und wird dort nicht mehr benutzt. Ein Umbenennen wäre
   über die Ressourcen möglich, war aber nicht Teil des Auftrags.

---

## 12. Nächste Schritte

`menu9` ist aufgespielt und verifiziert (Seitentaste öffnet die Modus-Auswahl,
kein Absturz). Offen ist nur noch:

1. **Kompletter Durchlauf am Gerät:** Modus mit den Seitentasten wählen, mit der
   Vordertaste bestätigen, zurück in die Vorschau, Foto **und** Video auslösen.
2. **Neustart-Test:** Nach einem Kaltstart muss das Menü wieder erscheinen und die
   Seitentaste wieder die Modus-Auswahl öffnen — das prüft, ob `S00zsdvcam` den
   Bind-Mount nach dem Boot korrekt setzt.
3. Falls etwas klemmt: Rückweg auf den vorherigen Stand mit
   ```sh
   cat /mnt/extsd/dbg/sdvcam_menu6.bin > /mnt/extsd/.sdvcam_patched
   ```
   Werkszustand: `.sdvcam_patched` löschen (oder `S00zsdvcam` entfernen) und neu
   starten — dann läuft wieder das Binary aus dem squashfs.

### Warum der Upload über die serielle Konsole so mühsam war

Für künftige Änderungen: **die SD-Karte am PC beschreiben ist der richtige Weg.**
Ein 3,4-MB-Transfer über die 115200-Baud-Konsole ist nicht praktikabel:

- Rohbytes über ein tty in canonical mode enthalten `0x03` (^C → `SIGINT`),
  `0x04` (^D → EOF) und `0x13`/`0x11` (^S/^Q → Flow-Control). Der Transfer
  bricht ab oder die Shell bleibt in der Heredoc hängen.
- `tools/push_uu.py` löst das mit uuencode (nur Zeichen `0x20..0x5F`) und
  blockweiser Übertragung an Zeilengrenzen. Der **Transport** funktioniert
  damit nachweislich (Größe exakt, Struktur korrekt), aber das `uudecode` auf
  dem Gerät bricht bei echten Binärdaten mit `short file` ab. Nicht
  weiterverfolgt — die Karte ist der schnellere Weg.
- Beim Kopieren am PC: Datei **nicht** direkt als `.sdvcam_patched` ablegen.
  Erst als `sdvcam_menu9.bin` kopieren, MD5 auf dem Gerät prüfen, dann
  `cat … > .sdvcam_patched`. Eine halb kopierte Datei an dieser Stelle bedeutet
  einen schwarzen Bildschirm.

---

## 13. Werkzeuge in diesem Repo

| Datei | Zweck |
|---|---|
| `tools/build_v9.py` | baut `menu9` aus `sdvcam_v8`, prüft jede Patchstelle vor dem Schreiben |
| `tools/thumb.py` | Thumb-2-Encoder für `BL` / `B.W`, gegen echte Werksbytes verifiziert |
| `tools/push_file.py` | Datei über die serielle Konsole hochladen (Heredoc) |
| `tools/sh.py` | Befehl auf der Kamera ausführen, Ausgabe abwarten |
| `tools/fbgrab2.py` | Framebuffer als ASCII (Zellmaximum, damit dünne Schriften sichtbar bleiben) |
| `tools/set_thresh.py` | Long-Press-Schwelle im laufenden Prozess setzen |
| `tools/keys.py` | evdev-Mitschnitte auswerten (Drücke, Haltezeiten, Prellen) |
| `tools/dis_cfg.py` | rekursiver capstone-Disassembler (nötig, weil `objdump` in `keyProc` desynchronisiert) |
| `tools/S00zsdvcam` | Init-Skript für den Bind-Mount |

**Werkzeug-Fallen, die dokumentiert bleiben sollten:**

- Das ELF hat **zwei** LOAD-Segmente mit unterschiedlichem Delta:
  `off 0 → vaddr 0x10000` und `off 0x26b67c → vaddr 0x28b67c`.
  Für `vaddr >= 0x28b67c` gilt `file_off = vaddr - 0x20000`.
- `objdump` desynchronisiert ab `0x5b8xx` (Daten im Codefluss) — für `keyProc`
  immer `dis_cfg.py` benutzen, sonst entstehen Patchvorschläge auf Bytes, die
  gar keine Instruktionen sind.
- BusyBox hat **kein** `grep -E`, kein `pgrep`, kein `--time-style`.
- Git-Bash verbiegt Gerätepfade (`/mnt/extsd/...` → `C:/Program Files/...`),
  wenn `MSYS_NO_PATHCONV=1` fehlt.
- Die App loggt **nicht** auf die Konsole, sondern nach `/tmp/log/sdvcam.INFO`
  (Symlink auf `LOG-SDV-<datum>-<zeit>`), weil `S01app` sie ohne Umlenkung
  startet. `/tmp` ist tmpfs — beim Ausschalten ist das Log weg.
- `poweroff -f` (Langdruck) hinterlässt die SD-Karte unsauber; die FAT-Warnung
  beim Boot ist normal und kein Defekt.

---

## 14. Reproduktion

```sh
python build_v9.py                       # erzeugt sdvcam_menu9.bin + MD5
python push_file.py sdvcam_menu9.bin /mnt/extsd/dbg/sdvcam_menu9.bin
# auf dem Gerät:
cat /mnt/extsd/dbg/sdvcam_menu9.bin > /mnt/extsd/.sdvcam_patched
md5sum /usr/bin/sdvcam
/etc/init.d/S01app start
```

Rückbau auf Werkszustand: `.sdvcam_patched` löschen (oder
`S00zsdvcam` entfernen) und neu starten — die Kamera läuft dann wieder das
Binary aus dem squashfs.

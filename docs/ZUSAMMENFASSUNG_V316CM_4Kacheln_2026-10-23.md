# Allwinner V316 Cam Actioncam — 4-Kachel-Menü: Zusammenfassung der Arbeiten

**Datum:** 2026-10-23
**Kamera:** Allwinner V316 Cam, SoC Allwinner V316 (`sun8iw12p1`), Linux 4.9.118 armv7l
**Ziel:** Beim Start direkt das 4-Kachel-Menü anzeigen, mit der Fronttaste durchblättern, mit OK bestätigen.

---

## 1. Ergebnis auf einen Blick

| Anforderung | Status |
|---|---|
| Fronttaste öffnet die 4 Kacheln | **funktioniert** |
| Durchblättern der Kacheln | **funktioniert** (Fronttaste und Seitentasten) |
| Auswahl mit OK-Taste | **funktioniert** |
| Menü automatisch beim Booten | **offen** (siehe Abschnitt 7) |

Aktueller Ablauf am Gerät: **Reboot → Vorschaubild → Fronttaste → 4 Kacheln → navigieren → auswählen.**

---

## 2. Umgebung und Zugang

| Punkt | Wert |
|---|---|
| Arbeitsverzeichnis | `D:\v316cm` |
| Debug-Zugang | UART über **COM11 @ 115200**, root-Shell (`/ #`) |
| Python mit pyserial | `D:\Phyton\python.exe` (pyserial 3.5) |
| ARM-Toolchain | `C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin` |
| Firmware-Binary | `sdvcam`, 3.407.624 Bytes, ELF32 ARM |
| Deploy-Pfad | `/mnt/extsd/sdvcam`, per `mount --bind` auf `/usr/bin/sdvcam` |
| UI-Ressourcen | `/mnt/extsd/custom_ui` → `/usr/share/minigui/res/images` |
| App-Start | `/etc/init.d/S01app` → `/usr/bin/sdvcam > /tmp/sdvcam.log 2>&1 &` |

**Referenzstände (MD5):**

| Datei | MD5 | Bedeutung |
|---|---|---|
| `sdvcam_v8` | `ee7425e348fc3d35d09ff62fc405860a` | sauberer Ausgangsstand |
| `sdvcam_4tiles_final` | `5ce4e6c6f7125394b099dae940f124ed` | **aktuell auf der Kamera** |

---

## 3. Adressabbildung — die wichtigste Regel

```
vaddr  =  datei_offset + 0x10000
datei  =  vaddr - 0x10000
```

Das gilt **für alles**: Code, Strings und Code-Caves.

- `objdump` mit `--adjust-vma=0x10000 --start-address=V` liest den **Datei-Offset `V - 0x10000`** und zeigt Adressen als Vaddr an.
- In einer `.s`-Datei muss `.org` die **Vaddr** sein. Beim Zurückschreiben ins Image gilt: `data[vaddr - 0x10000] = byte`.
- `.org`-Direktiven müssen **aufsteigend** sortiert sein, sonst: *"attempt to move .org backwards"*.
- **Falle:** Bytearray-Slice-Zuweisung mit einem kürzeren Slice **verkleinert** die Datei. Immer `len(data) == len(v8)` asserten.

**ELF-Programmheader:** Der erste `PT_LOAD` ist `R E` und reicht von `0x10000` bis `0x27b67c`. Alles darin ist ausführbar — auch Null-Padding in `.rodata`. Das ermöglicht Code-Caves.

---

## 4. Bewertung des ursprünglichen Plans (Schritte A–D)

| Schritt | Offset | Bewertung |
|---|---|---|
| **A** Boot-Hook in `OnWindowLoaded` | `0x5c0ee` | **falsch** — zu früh, siehe 5.1 |
| **B** Fronttaste blättert Kacheln | `0x59852` | **korrekt** |
| **C** OK-Dispatcher | `0x4afe0` | **korrekt** |
| **D** Fronttaste öffnet Menü | `0x4ba46` | **Ziel richtig, Weg falsch** — siehe 5.3 |

### Was an B und C stimmt

**B** (`0x59852`, `0x15` → `0x0b`): Die Funktion `FunctionSelectWindow::OnKeyEvent` nutzt eine `tbb`-Sprungtabelle bei `0x69850`. Der Eintrag an Index 2 zeigte auf `0x6987a` (Fenster verstecken, `0x15`). Mit `0x0b` zeigt er auf `0x69866` — denselben Zyklus-Code wie Index 4 (`subs r1, r5, #1` … `SetCurSel`). Ergebnis: Fronttaste blättert weiter.

**C** (`0x4afe0`, 76 Bytes): Die originale `FunctionChangeProc` hat die Signatur `(self = r0, ?, sel = r2)` — sie macht `mov r5, r2`. Der neue Dispatcher verwendet also den **richtigen** Register-Parameter. Er passt exakt in die 80 Bytes bis `0x5b030` (76 Bytes Code + 4 Bytes Literalpool).

---

## 5. Gefundene Fehler im Detail

### 5.1 Boot-Hook übergab das falsche `r0`

Der Hook in `PreviewPresenter::OnWindowLoaded` (Vaddr `0x6c0ee`) sprang nach `KeyFunctionProc` (`0x5b030`). Diese Funktion beginnt mit:

```asm
5b030:  push {r0, r1, r4, lr}
5b032:  mov  r4, r0            @ erwartet r0 = self
```

Zum Zeitpunkt des Hooks stand in `r0` aber das Ergebnis von `ldr.w r0, [r4, #0x90]` — ein **Kind-Objekt**, nicht der Presenter. `KeyFunctionProc` hätte also `[kind + 0x114]` gelesen.

### 5.2 Streaming-String war 32 Bytes, nicht 20

`/mnt/extsd/start_streaming.sh &` inklusive Nullbyte belegt **32 Bytes** (`0x1f32a2` bis `0x1f32c2`). Ein früherer Deploy schrieb nur 20 Bytes — daher der MD5-Mismatch.

### 5.3 `KeyFunctionProc` ist kein „Menü öffnen", sondern ein Wächter

Das war der eigentliche Knackpunkt. `KeyFunctionProc` (`0x5b030`) enthält bei `0x5b0b4` zwar den `Show()`-Aufruf:

```asm
5b0b4:  ldr.w r0, [r4, #0x114]   @ FunctionSelectWindow*
5b0b8:  ldr   r3, [r0]
5b0ba:  ldr   r3, [r3, #108]     @ Show()
```

Aber davor liegen mehrere Abbruchbedingungen:

| Adresse | Bedingung für Weiterlauf |
|---|---|
| `0x5b060` | Ergebnis von `0x5abd2` ≠ 1 |
| `0x5b07a` | `[self+0x17c] == 0` |
| `0x5b080` | `[self+0x160] == 0` |
| `0x5b086` | `[self+0x168] == 0` |

Schlägt eine fehl, kehrt die Funktion **stumm** zurück — kein Menü, kein Log, keine sichtbare Änderung. Genau das war beim Tastendruck zu beobachten: Der Framebuffer war byte-identisch.

### 5.4 Die Fronttaste ist nicht Key 132

Die Hardware liefert **`KEY_POWER` (116) auf `/dev/input/event1`** (Treiber `axp22x-powerkey`). Erst die App mappt intern auf 132 — sichtbar am Vergleich `cmp r5, #132` bei `0x5b99c`.

Nachgewiesen per `hexdump` auf allen vier Event-Geräten; nur `event1` feuerte. Der Tastenpfad läuft über `0x5ba38` → `0x5ba46`.

---

## 6. Die Lösung

### 6.1 Code-Cave

Null-Padding bei **Vaddr `0x1f5130`** (= Datei-Offset `0x1e5130`), 116 Bytes, liegt im ausführbaren `PT_LOAD`-Segment. Ursprünglich Nullen, direkt hinter dem String `/dev/mmcblk0`.

### 6.2 Der Stub

```asm
; Vaddr 0x1f5130
ldr.w   r0, [r0, #0x114]    ; r0 = self->func_win  (r0 hält hier noch self)
ldr     r3, [r0, #0]        ; vtable
ldr     r3, [r3, #108]      ; FunctionSelectWindow::Show()
bx      r3                  ; Tail-Call; lr wurde bei 0x5ba42 restauriert
```

Das umgeht **alle** Wächter aus 5.3. Wichtig: `r0` enthält an dieser Stelle noch `self`, weil `mov r0, r4` bei `0x5ba3e` vor dem Stackabbau erfolgt und `ldmia` nur `r4–r7` und `lr` berührt.

### 6.3 Endgültige Patch-Liste (`sdvcam_4tiles_final`)

| # | Vaddr | Datei-Offset | Länge | Inhalt |
|---|---|---|---|---|
| B | `0x59852` | `0x59852` | 1 | `0x15` → `0x0b` |
| C | `0x5afe0` | `0x4afe0` | 76 | 4-Kachel-Dispatcher |
| D | `0x5ba46` | `0x4ba46` | 4 | `b.w 0x1f5130` (`99 f1 73 bb`) |
| — | `0x1f5130` | `0x1e5130` | 10 | Show()-Stub (`d0 f8 14 01 03 68 db 6e 18 47`) |
| — | `0x2032a2` | `0x1f32a2` | 32 | `/mnt/extsd/start_streaming.sh &\0` |

**Ergebnis-MD5:** `5ce4e6c6f7125394b099dae940f124ed`

---

## 7. Autostart: warum es noch offen ist

Zwei Anker wurden getestet — beide sind beim Booten nicht brauchbar:

| Anker | Ergebnis |
|---|---|
| `OnWindowLoaded`, Vaddr `0x6c0ee` | `[self+0x114]` ist **NULL** → **SIGABRT**, `PC: 0x6c0f2` (das ist `ldr r3, [r0, #0]`) |
| Fenster-Init-Ende, Vaddr `0x48608` | `r4` ist dort **NULL** (Fehlerpfad) → **SIGSEGV bei Adresse 0x114**, `PC: 0x1f5146` |

Zusätzliche Erkenntnis aus dem Boot-Log: Während der gesamten Fenster-Initialisierung meldet der Window-Manager
`post boardcast event failed, ui have not inited, will be post later` — die UI ist zu diesem Zeitpunkt noch nicht bereit.

**Nächster sinnvoller Ansatz:** Ein Anker **nach** der Zuweisung `[presenter+0x114]` (bei Vaddr `0x485ac`, `str.w r0, [r4, #0x114]`), an dem `self` garantiert gültig ist. Kandidaten:

- `BoardcastModeInfo` (`preview.cpp:1158`) — läuft beim Boot nach der Fenstererzeugung
- Handler für `MSG_MODE_SWITCH_DONE` im `PreviewWindow` — wird erst nach UI-Init zugestellt

Beide Stellen laufen mehrfach, brauchen also ein **Einmal-Flag**. Achtung: `.text` ist nur `R E`, nicht beschreibbar — das Flag müsste in `.data` liegen.

---

## 8. Verifizierte Bedienung

- **Reboot** → Vorschaubild mit „Foto 8M"
- **Fronttaste** → 4 Kacheln: `1. FOTO / 2. VIDEO / 3. STREAM / 4. SETUP`
- **Seitentasten** → Navigation zwischen den Kacheln
- **OK** → Auswahl; der Dispatcher schaltet Foto-/Video-Modus, startet das Streaming-Skript oder öffnet die Einstellungen

Verifikation erfolgte ohne Blick auf das Display: Der Framebuffer (`/dev/fb0`, 320×480, 32 bpp BGRA) wurde über die serielle Konsole gelesen (gzip + uuencode) und lokal als PNG rekonstruiert.

---

## 9. Dateien in `D:\v316cm`

### Builds

| Datei | Inhalt |
|---|---|
| `sdvcam_v8` | sauberer Ausgangsstand (Referenz) |
| `sdvcam_4tiles_final` | **produktiver Stand** |
| `sdvcam_4tiles_v3` | Boot-Hook mit korrigiertem `r0` (verworfen) |
| `sdvcam_4tiles_v4` | direkter `Show()` im Boot-Hook (crasht) |
| `sdvcam_4tiles_v5` | B+C+D ohne Boot-Hook |
| `sdvcam_4tiles_v6` | wie final, aber mit Debug-Marker |
| `sdvcam_4tiles_v7` | Autostart-Versuch (crasht) |

### Skripte

| Datei | Zweck |
|---|---|
| `build_sdvcam_4tiles_final.py` | baut den produktiven Stand aus `sdvcam_v8` |
| `build_sdvcam_4tiles_v3…v7.py` | die jeweiligen Zwischenstände |
| `show_stub_final.s` | Assembler-Quelle des Show()-Stubs |
| `apply_build.py` | **generisches Deploy**: stellt v8 aus dem Geräte-Backup wieder her, patcht nur die Diff-Regionen per `dd`, prüft MD5, mountet und startet neu |
| `grab_screen.py` | liest `/dev/fb0` über die serielle Konsole und speichert ein PNG |
| `check_state.py` | prüft MD5 und Prozessstatus auf der Kamera |
| `probe_crash.py` | startet `sdvcam` mit Logfile und liest die Absturzadresse |
| `apply_v3.py` | älteres Deploy-Skript (durch `apply_build.py` ersetzt) |

**Deploy-Aufruf:**

```
D:\Phyton\python.exe apply_build.py "d:\v316cm\sdvcam_4tiles_final" 5ce4e6c6f7125394b099dae940f124ed
```

---

## 10. Rollback

Auf der Kamera liegt der saubere Stand als Backup:

```sh
cp /mnt/extsd/sdvcam_v8_bak /mnt/extsd/sdvcam
sync
/etc/init.d/S01app restart
```

Das Backup hat nachweislich MD5 `ee7425e348fc3d35d09ff62fc405860a`.

Zusätzlich lokal vorhanden: `V316CM_WORKING_FULL_IMAGE_16MB.bin` und `V316CM_WORKING_BACKUP_2026-10-22.zip`.

---

## 11. Offene Punkte

1. **Autostart der 4 Kacheln** — Anker siehe Abschnitt 7.
2. **Kachel 3 (STREAM)** — führt `/mnt/extsd/start_streaming.sh &` aus; das Skript liegt auf dem Gerät und sollte vor einem Einsatz im Feld geprüft werden.
3. **Nebenwirkung von Patch B** — Der `tbb`-Eintrag an Index 2 war ursprünglich „Fenster verstecken". Diese Funktion ist über diesen Index nicht mehr erreichbar. Bisher ohne beobachtete Auswirkung.
4. **Rückmeldung beim Booten** — Ohne Autostart bleibt der erste Tastendruck nötig.

---

## 12. Methodik (kurz)

1. Bestehenden Plan gegen das echte Binärbild geprüft (Disassembly aller vier Patch-Stellen).
2. Signatur von `FunctionChangeProc` und `KeyFunctionProc` aus dem Originalcode abgeleitet, statt sie anzunehmen.
3. Fehlschläge nicht geraten, sondern belegt — über `PC:`-Zeilen im glog-Absturzlog der App.
4. Tastenpfad empirisch nachgewiesen: `hexdump` auf allen Event-Geräten plus ein Marker-File im Patch-Stub.
5. Ergebnis ohne Display-Zugriff verifiziert: Framebuffer über die serielle Konsole ausgelesen und als PNG rekonstruiert.

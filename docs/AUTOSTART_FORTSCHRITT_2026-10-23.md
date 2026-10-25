# Autostart-Fortschritt — 2026-10-23 (Session 2)

## Aktueller Stand

Kamera läuft auf **v8 (clean)** — `sdvcam_4tiles_final` ist lokal verfügbar und per `apply_build.py` deploybar.
Skript `/mnt/extsd/autostart_tiles.sh` liegt auf der SD-Karte der Kamera.

## Neue Erkenntnis: Synthetic Key Press funktioniert!

**Entdeckung:** Man kann einen synthetischen KEY_POWER-Tastendruck direkt nach `/dev/input/event1` schreiben,
und sdvcam empfängt ihn als keyCode=132.

### Methode
- Linux input_event: `struct input_event { timeval(8B); type(2B); code(2B); value(4B) }` = 16 Bytes
- KEY_POWER = code 116, type=1 (EV_KEY), value=1 (press) / 0 (release)
- EV_SYN = type=0, code=0, value=0
- Vollständiges Event = press(16B) + syn(16B) + release(16B) + syn(16B) = 64 Bytes
- Shell-Kommando: `printf '\x00\x00...\x01\x00\x74\x00\x01\x00...' > /dev/input/event1`
- `xxd` und `base64` sind auf der Kamera NICHT verfügbar; `printf`, `uuencode -m`, `gzip` funktionieren

### Beweis
Log-Zeilen nach synthetischem Tastendruck:
```
window.cpp:218  <WindowProc>MSG_KEYDOWN
window.cpp:159  <WindowProc>MSG_KEYUP
window.cpp:180  <WindowProc>WINDOWID_PREVIEW '0xc23558' is hiden, ignore key event
preview_window.cpp:147  <keyProc>[fangjianjun]: ------>keyCode = 132 , inLongPress = 0
```

**Der Tastendruck erreicht `keyProc` mit keyCode=132 — genau wie die physische Taste!**

### Das verbleibende Problem
- `ShowPreview` schlägt beim Booten fehl: `fatal error! wait render start timeout`
- Dadurch ist das Preview-Fenster "hidden": `WINDOWID_PREVIEW is hiden, ignore key event`
- Trotzdem erreicht der Key-Code `keyProc` — aber es ist unklar, ob `Show()` (Patch D) in diesem Zustand die Kacheln anzeigen kann
- Die `autostart_tiles.sh` hat 5s sleep — muss evtl. auf 10-15s erhöht werden (UI braucht lange zum Init)
- 3 Tastendrücke mit 1s Abstand wurden gesendet, aber kein `FunctionSelectWindow::Show` im Log sichtbar

## Boot-Log-Analyse (neu)

Wichtige Boot-Sequenz aus `/tmp/sdvcam.log`:
```
ShowPreview>fatal error! wait render start timeout
display_control.cpp:291  <Show>camera is not on previewing
abstract_mode.cpp:212    <MediaInitUsingCfg>show preview failed, set busy until camera reinit done
PostBoardcastEvent>...MSG_MODE_SWITCH_DONE  (ui have not inited, will be post later)
OnWindowLoaded>current work mode[4]   ← UI ist jetzt bereit
```

## Was morgen zu tun ist

1. **autostart_tiles.sh anpassen**: Sleep auf 10-15s erhöhen (UI-Init abwarten)
2. **`sdvcam_4tiles_final` deployen** und dann autostart_tiles.sh laufen lassen
3. **Prüfen**: Erscheinen die 4 Kacheln nach dem synthetischen Tastendruck?
4. **Wenn ja**: Brauchen wir nur einen Weg, das Skript beim Boot automatisch zu starten
   - Option A: Binary-Patch — `system("/mnt/extsd/autostart_tiles.sh &")` an einer sicheren Stelle im Boot-Pfad
   - Option B: Falls eine `autorun.sh` o.ä. auf der SD-Karte gesucht wird
5. **Wenn nein**: Problem ist der "hidden" Preview-Window — muss Show() direkt aufgerufen werden
   - Dann zurück zum Binary-Patch-Ansatz mit Einmal-Flag in .data

## Dateien auf der Kamera
- `/mnt/extsd/autostart_tiles.sh` — Skript mit 5s sleep + synthetischem KEY_POWER
- `/mnt/extsd/sdvcam_v8_bak` — sauberes Backup (MD5 ee7425e348fc3d35d09ff62fc405860a)
- `/mnt/extsd/sdvcam` — aktuell v8 (clean)

## Disassembler-Erkenntnisse

- Funktion bei `0x6b83c`: hat `ldr.w r0, [r4, #0x114]` bei `0x6bacc`, aber **keine Caller** (tot)
- Funktion bei `0x7ba20`: hat `movw r2, #1158` (preview.cpp:1158), greift aber nicht auf `[r4+0x114]` zu
- `OnUILoaded` bei `0x6ae6c`: wird beim Booten **nicht aufgerufen** (Probe bestätigt)
- `OnWindowLoaded` bei `0x6c0e8`: ruft `0x6b74c` auf, hat `tbb`-Switch, loggt `preview.cpp:66e`

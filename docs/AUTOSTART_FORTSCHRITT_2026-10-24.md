# Autostart-Fortschritt — 2026-10-24 (Session 3)

## Kurzfassung

**Der richtige Anker ist gefunden: `PreviewWindow::OnWindowLoaded` in `preview.cpp`,
Hook-Adresse `0x6c0e8`.** Dort ist die UI fertig aufgebaut (die Kachel-Icons werden
in `function_select_window.cpp:129` geladen). Ein erster Versuch mit `[r4+0x114]`
crasht aber, weil `r4` hier **nicht** das `PreviewWindow` ist.

Kamera steht am Ende der Session wieder auf dem bewährten Build
`sdvcam_4tiles_final` (MD5 `5ce4e6c6f7125394b099dae940f124ed`), PID läuft, Display
zeigt das Kamerabild, Fronttaste öffnet die 4 Kacheln.

## Was diese Session geklärt wurde

### 1. U-Boot-Hänger (abgeschlossen)
Siehe `2026-10-24.md` im Memory-Ordner. Kein Defekt, `bootdelay=5` — beim Einschalten
keine Taste drücken und nichts über COM11 senden.

### 2. `MSG_MODE_SWITCH_DONE` ist zu früh (bestätigt)
Probe-Build `sdvcam_4tiles_probe2` (Hook `0x5caee`) zeigte: `[self+0x114]` ist dort
gültig, das Event kommt genau **1×** pro Boot — aber ein direktes `Show()` crasht bei
`0x56d32` (`ldr r3,[r0]`, Objekt noch nicht konstruiert).
Log-Beleg: `PostBoardcastEvent>post boardcast event failed, ui have not inited,
will be post later, msg: MSG_MODE_SWITCH_DONE`.

### 3. Neuer Anker `0x6c0e8` (Funktion `preview.cpp` `OnWindowLoaded`)
Funktion ab `0x6c018`, loggt
`preview.cpp:155 <OnWindowLoaded>current work mode[%d]`.
Struktur:
```
0x6c018  push {r0,r1,r2,r4,r5,lr}; mov r4, r0
0x6c02c  ldr.w r3,[r4,#148]          ; 0x94 = work mode
0x6c030  cmp r3,#9 / cmp r3,#8       ; Sonderfaelle
0x6c054  log "current work mode[%d]"
0x6c076  ldr.w r3,[r4,#148]; cmp r3,#7; tbb [pc,r3]
0x6c08a  mode 0..3:  [r4+0x80] + bl 0x6236c
0x6c09e  mode 4..7:  [r4+0x90]->vtable[16]()
0x6c0a8  3x Fenster-Hide/Show ueber r4+0x5c
0x6c0e8  ldr.w r0,[r4,#0x90]         ; <-- HOOK-PUNKT
0x6c0ee  [r0]->vtable[30](11, 0)     ; Fenster mit id 11 zeigen (Preview)
0x6c0fe  add sp,#12; pop {r4,r5,pc}
```

### 4. Wichtig: `r4` ist NICHT das `PreviewWindow`
Probe `sdvcam_4tiles_probe3` (Hook `0x6c0e8`, nur `cbz`-Test) → `/tmp/OL_OK`,
also `[r4+0x114] != 0`.
Der echte Autostart-Build `sdvcam_4tiles_autostart_v2` las dann `[r4+0x114]` und
crashte bei **`PC: 0x1f5166`** (`ldr r3,[r0]`) → der Wert ist **non-NULL, aber kein
gültiger Zeiger**. `preview.cpp`-`OnWindowLoaded` arbeitet also auf einem anderen
Objekt als `PreviewWindow::HandleMessage` (`0x5ca28`).

Gemeinsamkeiten mit `BoardcastModeInfo` (`0x7ba20`): beide nutzen `[r4+0x90]`,
`[r4+0x94]`, `[r4+0x98]` — also dieselbe Klasse (`Preview`-Modell, nicht das Fenster).

### 5. Arbeitshypothese für morgen
`[r4+0x90]` **ist** das `PreviewWindow` — der Originalcode zeigt genau dieses Fenster
mit id 11 (= `WINDOWID_PREVIEW`) an. Also:
```
w  = [r4+0x90]
fs = [w+0x114]      -> FunctionSelectWindow
Show(fs)            -> 4 Kacheln
```

## Gebaut, aber noch NICHT getestet

`D:\v316cm\sdvcam_4tiles_autostart_v3`
**MD5 `6a316b10893a3eb5d1ed82c5cb60e0ce`**

Stub @ `0x1f513c` (100 B, Cave-Ende `0x1f51a4`, 4 B Reserve), Ablauf:
1. Original: `[r4+0x90]->vtable[30](11, 0)`
2. Einmal-Flag `/tmp/AS` per `access()`; fehlt es → `system("touch /tmp/AS")`
3. `w = [r4+0x90]`; `fs = [w+0x114]`; Sanity-Check `fs >= 0x10000`
4. `bl 0x1f5130` (bestehender Show-Stub, wiederverwendet)

Deployen mit:
```
D:\Phyton\python.exe apply_build.py "d:\v316cm\sdvcam_4tiles_autostart_v3" 6a316b10893a3eb5d1ed82c5cb60e0ce
```
Vorher `rm -f /tmp/AS`.

**Wenn es crasht:** PC im Log (`glog_helper.cpp:16] PC: @ 0x...`) sagt, welcher
Schritt es war. Dann ist `[r4+0x90]` nicht das PreviewWindow und wir brauchen einen
zweiten Hook auf `PreviewWindow::HandleMessage` (`0x5ca28`, dort ist `[self+0x114]`
definitiv gültig) mit dem Flag aus `OnWindowLoaded`.

## Adressen / Referenzen (diese Session verifiziert)

| Sache | Wert |
|---|---|
| `system@plt` (ARM-Stub) | `0x1c94c` |
| `access@plt` (ARM-Stub) | `0x1cc3c` |
| Code-Cave | `0x1f5130` .. `0x1f51a3` (116 B), belegt: `0x1f5130`–`0x1f5139` Show-Stub |
| Nach der Cave | ab `0x1f51a4` Strings (`"RemoveFile"`, `"IsMounted"`, ...) |
| `PreviewWindow::HandleMessage` | `0x5ca28`, `[self+0x114]` gültig |
| `MSG_MODE_SWITCH_DONE`-Zweig | `0x5caee` (zu früh für Show) |
| `OnWindowLoaded` (preview.cpp) | `0x6c018`, Hook am Ende `0x6c0e8` |
| Show-Stub | `0x1f5130`: `ldr.w r0,[r0,#0x114]; ldr r3,[r0]; ldr r3,[r3,#108]; bx r3` |
| `objdump` | **ohne** `--adjust-vma` benutzen, sonst +0x10000 verschoben |

### Cave-Platz ist der Engpass
Nur 104 freie Bytes (`0x1f513c`..`0x1f51a4`). Die großen Zero-Runs in `.rodata`
(z. B. `0x2260f4`, 272 B) sind **echte Datenarrays** (ringsum Zahlenwerte) — nicht
als Cave verwendbar.

## Hilfsskripte, die diese Session entstanden sind

| Datei | Zweck |
|---|---|
| `sh.py` | beliebige Shell-Kommandos über COM11 absetzen (`python sh.py "cmd" ...`) |
| `restart_watch.py` | sdvcam neu starten, Log leeren, serielle Ausgabe mitschneiden |
| `probe_onwindowloaded.s` / `build_probe_ol.py` | Probe an `0x6c0e8` |
| `autostart2_stub.s` / `build_autostart2.py` | v2 (crasht, `[r4+0x114]`) |
| `autostart3_stub.s` / `build_autostart3.py` | v3 (gebaut, ungetestet) |

## Nächste Schritte

1. `sdvcam_4tiles_autostart_v3` deployen und testen.
2. Falls Crash: zweiter Hook auf `0x5ca28` (`HandleMessage`) + Flag aus `OnWindowLoaded`.
3. `start_streaming.sh` für Kachel 3 vor Feldeinsatz prüfen.
4. Nebenwirkung von Patch B beobachten (tbb-Eintrag Index 2 „Fenster verstecken"
   nicht mehr erreichbar).

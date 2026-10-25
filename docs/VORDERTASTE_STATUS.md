# Vordertaste = Auslöser — Stand und offene Punkte

**Status: UNFERTIG.** Zuletzt bearbeitet 2026-10-25 (Session 6.5/6.6).
Deployt ist `sdvcam_menu_v14`. Die Vordertaste löst **noch nicht** aus.

> **Korrektur am Abend (18:06):** Die Vordertaste hat **vier**, nicht drei
> Hauptfunktionen. Der User: *„die Rollen von OK-Taste und Vordertaste sind
> unklar. Insbesondere die Vordertaste hat nur 4 Hauptfunktionen, die müssen
> wir erstmal herstellen. Das hat Priorität."*
>
> | # | Funktion | Wann |
> |---|---|---|
> | 1 | **Einschalten** | aus → 1× drücken |
> | 2 | **Auslösen** | läuft, im Vorschaubild |
> | 3 | **Zurück ins Obermenü** | in Untermenüs |
> | 4 | **Ausschalten** | läuft + lang drücken |
>
> Damit ist die Vordertaste **kontextabhängig**: im Untermenü = Navigation,
> im Vorschaubild = Auslöser. Das deckt sich mit der Stock-Rolle (132 =
> Close/Zurück), ergänzt um den Auslöser in der obersten Ebene.

---

## 1. Zielvorgabe des Users (maßgeblich, wortgleich)

> *„die vordertaste soll nur 3 funktionen haben, drücken 1mal im
> ausgeschalteten zustand = einschalten, im Betrieb = Auslöser, lang drücken
> im betrieb = ausschalten. die ok taste führt duch die menüs, wobei einmal
> drücken = auswählen, 2mal kurz zurück ins obermenü. die seitentasten
> navigieren durch die menüs. ganz einfach"*

**Am Abend korrigiert auf 4 Funktionen** — siehe Hinweis oben am Dokusanfang.
Die kontextabhängige Deutung (Untermenü → zurück, Vorschau → Auslöser) ist die
Arbeitsgrundlage für morgen.

| Taste | Zustand | Aktion |
|---|---|---|
| Vorder (132) | aus | 1× → einschalten |
| Vorder (132) | läuft, Vorschau | kurz → **Auslöser (Foto)** |
| Vorder (132) | läuft, Untermenü | kurz → **zurück ins Obermenü** |
| Vorder (132) | läuft | lang → **ausschalten** |
| OK (130) | Menü | 1× → auswählen |
| OK (130) | Menü | 2× schnell → zurück ins Obermenü |
| Seitentasten | Menü | navigieren |

**Wichtig:** In der **Stock-Firmware** ist 132 laut `tbb`-Tabelle @ `0x69850`
**„Close/Zurück"** (`0x6987a`) und 130 **„bestätigen"** (`0x69884`). Die
Vordertaste war also nie der Auslöser — das ist eine **Umbelegung**, keine
reine Routen-Reparatur.

---

## 2 Was funktioniert

| Sache | Status | Beleg |
|---|---|---|
| 4-Kachel-Menü beim Boot | ✅ | FB-Hash `882fff0d930173964f5fab73ca2627ce` = Menü |
| Moduswechsel FOTO | ✅ | User-bestätigt („unten steht Foto") |
| OK-Taste: Menü → Vorschau | ✅ | User-bestätigt |
| Vordertaste erreicht `keyProc` | ✅ | Log: `keyCode = 132 , inLongPress = 0` |

## 3 Was nicht funktioniert

| Sache | Status | Beleg |
|---|---|---|
| **Vordertaste → Foto** | ❌ | 38 Fotos vor UND nach dem Test, neueste `ANMP0011.jpg` |
| **OK-Taste → Foto** | ❌ | kein `take pic` / `TakePictureWithType` im Log, je |
| Langdruck → Ausschalten | ❌ ungetestet | — |

---

## 4 Der patch in v14

`PreviewWindow::keyProc` @ `0x5b83c` hat bei `0x5b888` ein Gate, das **vor**
den drei in v12 gepatchten Stellen liegt:

```asm
0x5b888: ldr.w  r3, [r4, #0x17c]
0x5b88c: cbz    r3, 0x5b8c6        ; [+0x17c]==0 -> normale Weiterleitung
0x5b88e: sub.w  r3, r5, #0x3b ; cmp r3,#2 ; bls 0x5b8c6
0x5b896: cmp    r5, #0x84          ; Taste 132 ?
0x5b898: bne    0x5b89e            ; nicht 132 -> OK-Pfad
0x5b89a: cmp    r6, #1
0x5b89c: beq    0x5b8c6            ; 132 + LANG -> normale Weiterleitung
0x5b89e: ldr.w  r3, [r4, #0x160]
0x5b8a2: cbz    r3, 0x5b8b0
0x5b8a4: -> 0x5ba3c (Show)         ; 132 + KURZ -> Kachelmenue anzeigen
```

Solange `[+0x17c]!=0` und `[+0x160]!=0` landete jede kurze 132 im Show-Zweig.
Deshalb „manchmal schliesst es sich, aber nicht immer".

**v14 = v12 + ein Zweig** — 4 Bytes bei `0x5b89a`:

```
vorher:  012e 13d0    cmp r6,#1 / beq 0x5b8c6
nachher: 00f0d6b8    b.w 0x5ba4a
```

`0x5ba4a` ist der Auslöse-/Poweroff-Handler und macht bereits die Spec:
`cmp r6,#1` → lang → `system("poweroff -f")`, kurz → `CloseTopWindow()×3` +
`PostMsg(self,self,81,1)`.

Encoding erzeugt mit `arm-none-eabi-as` (`tools/asm/brC.s`, `.fill 428`) und mit
capstone gegen `#0x5ba4a` verifiziert. Taste 130 zweit schon bei `0x5b898`
(`bne 0x5b89e`) vor dem Patch ab.

**Ergebnis: Die Vordertaste erreicht jetzt zwar den Auslöse-Handler, es kommt
aber trotzdem kein Foto.** Siehe §5.

---

## 5 Der eigentlich offene Fehler: die Aufnahme schlägt fehl

Der Auslöser wird augenscheinlich angestoßen, aber es entsteht keine Datei.

### 5.1 harte Belege

* Fotoanzahl konstant 38 (`ANMP0008`–`ANMP0011` sind alt)
* Kein `take pic` / `TakePictureWithType` / `capture` im Log — **je**
* `grep -c keyCode /tmp/sdvcam.log` = 3, davon zwei× `132, inLongPress = 0`
* App läuft in `normal_capture_mode`:
  ```
  normal_capture_mode.cpp:663  <SetCameraRawFormat> set camera raw value[0]
  normal_capture_mode.cpp:918  <UpdatePicCountInfo> resolution[4] avail[29555] remain_count [13434]
  ```

### 5.2 Hauptverdacht: Speicher-Allokation schlägt fehl

Im **Kernel-Log** (nicht App-Log!) genau **zweimal**:

```
[  124.549414] In ion_carveout_heap_allocate line 89: alloc buffer size: 7991296 Byte fail!
[  128.252274] In ion_carveout_heap_allocate line 89: alloc buffer size: 7991296 Byte fail!
```

* ~7,6 MB aus dem ion-carveout-Heap
* Zeitpunkt fällt mit den Tastendrücken zusammen (App-Glog-Uhr startet bei
  `00:00:00` zum App-Start; `keyCode = 130` bei `00:00:43`, `132` bei
  `00:01:03` und `00:01:06` — Kernelzeit 124 s ≈ Glog 43 s)
* Speicherlage ist knapp:
  ```
  MemTotal:     46628 kB      (nur 45 MB!)
  MemFree:       2296 kB
  MemAvailable: 21352 kB
  ```
* `setting_control.cpp:34 <SettingCtrl> 128M DRAM SCHEME set media last capture 4`

### 5.3 Nebenbefund

Im Medienordner liegen **8 Videodateien** (`ANMR*.mp4/.sec/.thm`). Video-
Aufnahme funktioniert also — nur die **Foto-Aufnahme** hängt. Das passt zum
Verdacht: Video nutzt vorab reservierte Puffer, das Foto braucht offenbar eine
frische 7,6-MB-Allokation.

### 5.4 Der Modus ist korrekt — es liegt nicht an der Moduswahl

Zum Zeitpunkt der Sicherung zeigte der Framebuffer Hash
`882dcd6d841c073d1be2f56d27c132b4` = **Foto-Vorschau mit Bottom-Bar „Foto“**
(dokumentierter Referenzhash). Die Kamera stand also echt im Fotomodus mit
sichtbarem Vorschaubild, als die Vordertaste gedrückt wurde.

→ Der Fehler liegt **nicht** in der Moduswahl, sondern in der Ausführung der
Aufnahme.

---

## 6 Nächste Schritte (priorisiert)

1. **Handler für Nachricht 81 finden.** `PreviewWindow::HandleMessage` @
   `0x5ca28` auseinandernehmen und verfolgen, was nach
   `PostMsg(self,self,81,1)` passiert. Werkzeug: `dis_cfg.py`.
2. **Die 7.991.296-Byte-Anforderung zurückverfolgen.** Wer allokiert das?
   Verdacht: `normal_capture_mode.cpp`. Mit `grep`/`strings` im Binary nach
   der Größe und nach `ion_alloc`/`sunxi_ion_alloc` suchen.
3. **Stock-Verhalten isolieren.** Sauberes `sdvcam_v8` deployen und prüfen, ob
   die OK-Taste (130) dort überhaupt ein Foto macht. Damit ist klar, ob die
   Capture-Pipeline grundsätzlich intakt ist oder unsere Patches sie stören.
4. **Speicherdruck prüfen.** Was verbraucht die 45 MB? Ggf. einen Prozess
   stoppen (z. B. Streaming/OTA) und den Auslöser erneut testen.
5. **Einschalten aus dem Aus-Zustand** prüfen — liegt in Kernel/PMIC, nicht in
   der App. `/sys/class/wakeup/`, `axp22x-powerkey`, gpio-keys-DTS.

---

## 7 Rollback

Alle Builds liegen in `firmware/sdvcam/`. Deployen über die SD-Karte:
beide Bind-Mounts lösen, Datei schreiben, `sync`, MD5 prüfen, neu mounten.

| Build | MD5 | Bedeutung |
|---|---|---|
| `sdvcam_v8` | `ee7425e348fc3d35d09ff62fc405860a` | saubere Stock-Referenz |
| `sdvcam_menu_v11` | `0ff4ffd99cb8377d9fe28cecc34d5dde` | letzter bekannter Gutstand |
| `sdvcam_menu_v12` | `0cda61d46070f20fa367310a5384d4ec` | v11 + Patches A/B/C |
| `sdvcam_menu_v13` | `d4c4a88eb2c6929f125c920e2c4f08da` | **KAPUTT — nicht deployen** (Patch D2 falsch kodiert, T1-`beq` erreicht 0x5ba4a nicht) |
| `sdvcam_menu_v14` | `7222f8d7f74767911747e92f019fa537` | **aktuell deployt** |

Bau-Skripte: `tools/menu_v12/build_menu_v14.py`, Deploy: `tools/menu_v12/deploy_v14.py`.

---

## 8 Fallen, die uns heute gebissen haben

* **`objdump` desynchronisiert in `keyProc`** → immer `tools/dis_cfg.py`
  (capstone, rekursiv) benutzen.
* **T1-Kurzverzweigungen nur ±256 B** — `imm8` ist **signed**. 0x5ba4a ist von
  0x5b89c aus 428 B entfernt und passt nicht in 2 Bytes. Deshalb in v13 der
  Fehler: `beq` landete bei `0x5b84a` statt `0x5ba4a`.
* **`arm-none-eabi-as` zählt `b.w` als 4 Bytes.** Der `.fill`-Abstand muss
  `ziel − (patch + 4)` sein, nicht `ziel − patch − 2`.
* **Serieller Verkehr bricht den U-Boot-Autoboot ab** → Kamera hängt bei
  `sunxi#`. Rettung: `reset` senden, dann **passiv** mitlesen, nichts senden.
* **Die Kamera hat nur 45 MB RAM** (`MemTotal 46628 kB`). Alles was große
  Puffer will, ist verdächtig.
* App nie von Hand starten ohne `killall -9 sdvcam` — Doppelinstanz crasht und
  das Log wird neu geschrieben.

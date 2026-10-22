# Allwinner V316 Cam / Allwinner V316 - Statusbericht & Analyse der Tasten & Menüs

## 1. Hardware-Status der Tasten (Messungen & Fakten)

1. **Vordere Taste (Einschalten / Modus / Zurück):**
   - **Befund:** Hardware-Defekt (physisch defekt / kein Kontakt).
   - **Überprüfung:** 
     - Direkter Bit-Scan der physikalischen Allwinner-GPIO-Register (PA, PB, PC, PD, PE, PF, PG, PH, PL via `/sbin/devmem`): 0 Bitänderungen bei Tastendruck.
     - Überwachung aller 4 Linux-Input-Devices (`/dev/input/event0` bis `event3`): 0 Bytes, 0 Interrupts.
     - **Ergebnis:** Die vordere Taste kann für die Bedienung definitiv nicht verwendet werden. Alle Funktionen müssen über die 3 verbliebenen Tasten abgebildet werden.

2. **Funktionsfähige Tasten:**
   - **Obere OK-Taste:** `/dev/input/event2`, Linux Keycode `139` (`KEY_RECORD`/`KEY_SELECT`, in MiniGUI Code `130`).
   - **Seitentaste OBEN (UP):** `/dev/input/event0`, Linux Keycode `115` (`KEY_VOLUMEUP`, in MiniGUI Code `136`).
   - **Seitentaste UNTEN (DOWN):** `/dev/input/event0`, Linux Keycode `114` (`KEY_VOLUMEDOWN`, in MiniGUI Code `135`).

---

## 2. Erreichte Meilensteine

1. **Automatischer SD-Boot & Persistenz (`/etc/init.d/S01app`):**
   - Warte-Schleife für `/dev/mmcblk0` implementiert. Bind-Mount von `/mnt/extsd/custom_ui` nach `/usr/share/minigui/res/images` und `/mnt/extsd/sdvcam` nach `/usr/bin/sdvcam` läuft bei jedem Systemstart automatisch.
2. **Deutsche Klartext-Kacheln:**
   - 4 Hauptkacheln (159x119): **MODUS**, **ALBUM**, **SETUP**, **ZURÜCK**.
   - 8 Modusauswahl-Kacheln (80x90) mit sauberer Typografie & Silbentrennung (z. B. **ZEIT-RAFFER**, **SERIEN-BILD**).
3. **Menüaufruf ohne Fronttaste:**
   - Tastendruck auf **Seite UP** im Livebild öffnet zuverlässig die 4 Hauptkacheln.

---

## 3. Offene Probleme & Ursachenanalyse

### Problem A: USB-Lademodus / Massenspeichermodus Pop-up bei Boot
- **Symptom:** Nach dem Start / Reboot erscheint wieder das Fenster *"Lademodus / Massenspeichermodus"* (`USBModeWindow`).
- **Ursache:** 
  1. In `build_v5.py` sprang Patch 1 an Offset `0x4ed64` irrtümlich direkt zu `0x4ed6a` – genau an den Einsprungpunkt, der das USB-Fenster *erzwingt*, anstatt ihn zu überspringen!
  2. Zusätzlich startet `sdvcam` an Adresse `0x4e29a` nach 1 Sekunde Verzögerung einen Thread, der das Fenster mit ID `0x974` (`WINDOWID_USB_MODE`) anfordert, weil die Kamera mangels Akku per USB mit Strom versorgt wird.
- **Lösung für morgen:**
  - `0x4ed64` auf `b #0x4ef10` setzen (sofortiger Exit aus dem USB-GUI-Handler).
  - `0x4e29a` auf `movs r0, #0; bx lr` patchen (sofortiger Abbruch des USB-Window-Threads).
  - Dadurch ist das USB-Pop-up permanent und vollständig deaktiviert.

### Problem B: Gefangen in der Modusauswahl ("zurück"-Verhalten)
- **Symptom:** Wenn der Benutzer auf "Modus" (Kachel 0) klickt, öffnen sich die 8 Unter-Kacheln (Video, Foto etc.). Wählt man einen Modus mit OK aus, bleibt man im Menü bzw. kehrt zu den 4 Hauptkacheln zurück, statt direkt im Livebild zu landen. Wenn man versehentlich im Modusmenü ist, gibt es ohne Fronttaste keine Abbrechen-Taste.
- **Ursache:**
  - `ModelSelectWindow::ItemClick` (`0x5abac`) schließt nur sich selbst (`0x58c1c`), belässt aber das übergeordnete `FunctionSelectWindow` (die 4 Kacheln) offen im Hintergrund.
  - Ursprünglich war die Fronttaste für "Abbrechen / Zurück" zuständig (Keycode 132).
- **Lösung für morgen:**
  1. **Nach Modusauswahl direkt ins Livebild:** In der Callback-Funktion `0x5abac` nach dem Umschalten auch `FunctionSelectWindow` schließen bzw. `OpenWindow(WINDOWID_PREVIEW)` ausführen.
  2. **Abbrechen im Modusmenü:** Langes Drücken der OK-Taste (1s) im Modusmenü mit Keycode 132 belegen (`ModelSelectWindow::CloseWindow` ohne Modusänderung).
  3. **Ausschalten (Power-Off):** Langes Drücken der OK-Taste (3s) im Livebild führt sauberes `poweroff -f` aus.

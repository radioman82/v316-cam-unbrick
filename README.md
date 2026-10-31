# Allwinner V316 Cam: Recovery und eigenständige Firmware

Stand: **31.10.2026**. Dokumentation und Werkzeuge für das reparierte Board
mit 16-MiB-Fudan-SPI-Flash (`a1 40 18`). FEL meldet es als Allwinner V536.

Die Kamera startet vollständig aus dem internen Flash. Die SD-Karte ist
ausschließlich Medienlaufwerk; App, Menüs, Übersetzungen, Bilder, WLAN und
Streaming benötigen keine Systemdateien auf SD.

## Geprüfter Funktionsstand

- Vier Kacheln: **FOTO · VIDEO · STREAM · SETUP**, automatischer Menüstart.
- Deutsche Menüs, einheitliches Setup und korrigierte Moduskacheln.
- „Flimmerreduzierung“ statt „Netzfrequenz“; sichtbare Fototexte mit „Foto“.
- Eigene Start-/Abschaltbilder: 320 × 240 Pixel, unkomprimiertes 24-Bit-BMP.
- Kaltstart, Menüs und WLAN/Livebild **ohne SD-Karte** geprüft.
- Webplayer mit Start/Pause, Vollbild, Bildrate und JPEG-Qualität.
- Foto und kurzes Video auf leerer Medien-SD aufgenommen und vollständig
  dekodiert; anschließend wieder funktionierendes Livebild.
- Betrieb während dieser Prüfung über externe Versorgung ohne Akku.

Der Stream zeigt die Display-Vorschau mit 320 × 240 Pixeln. **Das Display
muss angeschlossen sein:** Ohne Display lieferte der getestete Aufnahmeweg
schwarze Bilder. Native Album-Bedienung, Tonqualität und alle weiteren
Aufnahme-Untermodi sind nicht separat geprüft.

[Aktueller Stand](docs/INTERNES_IMAGE_2026-10-31.md) ·
[Bauen](docs/BUILD.md) · [Sichern und Wiederherstellen](docs/RECOVERY.md).

Neue Hardwarefotos: [UART-/FEL-Anschlüsse](pictures/zus%C3%A4tzliche-anschl%C3%BCsse.jpg),
[FEL-Nahaufnahme](pictures/FEL.jpg), [Antennenanschluss](pictures/Antennenanschluss.jpg).

## Repository

| Pfad | Zweck |
| --- | --- |
| `tools/ui_theme/` | Aktueller Renderer, Übersetzungen, Ressourcen-Builder |
| `tools/streaming/` | Streaming-/Webquellen; Legacy-SD-Installer |
| `tools/build_internal_image.py` | Internes 16-MiB-Image bauen |
| `tools/verify_internal_image.py` | Dateisystem, Bibliotheken und XZ prüfen |
| `tools/camera_uart.py`, `tools/sh.py`, `tools/logger.py` | UART-Zugang |
| `tools/capture_runtime.py`, `tools/backup_internal.py` | Private Sicherungen |
| `firmware/sdvcam/` | Nur die zwei benötigten App-Build-Basen |
| `firmware/ui_theme/` | Bisheriger öffentlicher SD-App-/Ressourcenstand |
| `firmware/splash/` | Vorbereitete Start-/Abschaltbilder |
| `firmware/V316CM_WORKING_FULL_IMAGE_16MB.bin` | Ältere funktionierende **Rettungsbasis**, nicht das neue Komplettimage |
| `firmware/kernel_rodata_exact.uImage` | Kernel mit passender Flash-Erkennung |
| `hardware/`, `pictures/`, `custom_ui/` | Hardwarebelege, Menübilder, Kacheln |

Das neue getestete Komplettimage enthält gerätespezifische WLAN-Daten und
bleibt lokal. Es ist kein öffentliches Universalimage. Die Build-Anleitung
beschreibt die benötigten eigenen Eingabedateien.

## Flash-Aufteilung

| Offset | Größe | Bereich |
| --- | --- | --- |
| `0x000000` | 1 MiB | Bootloader |
| `0x100000` | 3 MiB | Kernel |
| `0x400000` | 10,5 MiB | RootFS, jetzt XZ-SquashFS |
| `0xE80000` | 512 KiB | Einstellungen/JFFS2 |
| `0xF00000` | 128 KiB | U-Boot-Umgebung |
| `0xF20000` | 384 KiB | Startbild |
| `0xF80000` | 512 KiB | UDISK |

Das neue RootFS belegt 9.924.608 Byte und passt ohne neue Partitionierung.
Die ursprüngliche Kernelkorrektur ersetzt die fest eingetragene
Winbond-Erkennung `ef 40 18` durch die zum Board passende ID `a1 40 18`;
Kernel- und uImage-Prüfsummen werden neu aufgebaut.

## Bereinigung und Lizenz

Alte Probeprogramme, Zwischen-Binaries, Rohlogs, Chatkopien und überholte
Statusberichte wurden entfernt. Sie bleiben über die Git-Historie verfügbar.
Aktuelle Build-Abhängigkeiten und Rettungsbasen bleiben erhalten. Private
Sicherungen, Zugangsdaten und Testaufnahmen gehören nicht ins Repository.

Unabhängiges Reparatur-/Interoperabilitätsprojekt, nicht mit Allwinner
verbunden. Eigene Werkzeuge/Dokumentation: [MIT](LICENSE). Linux: GPLv2;
Fremdkomponenten behalten ihre jeweiligen Lizenzen. Die MIT-Lizenz ist keine
Neulizenzierung der herstellerspezifischen Firmwarebestandteile.

# Livevideo

Aktuell: [interne Firmware](../../docs/INTERNES_IMAGE_2026-10-31.md).
WLAN, HTTP und Livebild funktionieren ohne SD. Laufzeitkomponenten liegen
unter `/opt/cam`, WLAN-Konfiguration unter `/data/wlan.conf`.

Der Webplayer bietet Start/Pause, Vollbild, Neuverbinden, Bildrate und
JPEG-Qualität; er löst keine Aufnahmen aus. `fps`: 1–25, `quality`: 20–90.
15 Bilder/s bleiben der Standard; 25 Bilder/s sind eine experimentelle
Obergrenze. Beim Gerätetest am 01.11.2026 wurden bei JPEG-Qualität 65 sowohl
mit angeforderten 15 als auch mit 25 Bildern/s etwa 11–12 Bilder/s gemessen.
Jeweils 60 JPEGs waren vollständig dekodierbar und unterschiedlich.
Die Ausgabe zeigt die Display-Vorschau samt UI mit 320 × 240 Pixeln ohne Ton.
**Das Display muss angeschlossen sein**; ohne Display waren die JPEGs schwarz.

Die Videoeinstellung 1080p/30 oder 720p ändert diese Streamauflösung nicht.
Eine kleinere Aufnahmeauflösung könnte die Kamera indirekt entlasten;
ein Auflösungsvergleich wurde noch nicht gemessen. Der Capture-Pfad wartet
weiterhin 55 ms auf die Display-Aufnahme, hinzu kommen JPEG-Kodierung und
Übertragung. Die höhere Auswahl allein beschleunigt diesen Pfad nicht.

Endpunkte: `/`, `/cgi-bin/stream` (MJPEG), `/cgi-bin/snapshot` (JPEG).

## Quellen und Wartung

    python tools/streaming/build.py --zig PATH/TO/zig.exe

Zig 0.14.1 erzeugt statische ARMv7-Linux-Programme. Der JPEG-Header wird
per SHA-256 geprüft; Herkunft und Lizenz: `vendor/SOURCE.txt` und Header.
`display_capture.h` verwendet Allwinner disp2 und ION; ein eigener DMA-Puffer
und `flock` koordinieren parallele Captures. Der langsamere `capture_dump`-
Fallback entfernt seine temporäre Datei vor jeder Aufnahme.

Die getestete interne Firmware übernimmt die funktionierenden Dateien aus
der privaten Laufzeitsicherung (`ct9000-mjpeg`, `ct9000-control`). Öffentliche
Quellen erzeugen `v316cm-*`. Diese Varianten nicht ohne passende CGI-Pfade
mischen. Ein Quell-Neubau ist nicht automatisch erneut am Gerät geprüft.

`deploy.py` ist der ältere SD-Installer. Seine Hilfsklasse `Camera` unterstützt
beim internen Image `busybox='/opt/cam/bin/busybox'`. Die Shellskripte im
Quellbaum beschreiben den SD-Ausgangspunkt; der interne Builder schreibt
ihre Pfade nach `/opt/cam` beziehungsweise `/data` um.

Root-Kommando-CGI und Telnet sind vorhandene Wartungszugänge für das eigene
vertrauenswürdige Netz; keine Router-Portfreigabe ins Internet einrichten.

ABI-Referenz: [Allwinner disp2 Capture](https://github.com/Allwinner-Homlet/H6-BSP4.9-linux/blob/master/drivers/video/fbdev/sunxi/disp2/disp/de/disp_capture.c).

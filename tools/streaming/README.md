# Livevideo

Aktuell: [interne Firmware](../../docs/INTERNES_IMAGE_2026-10-31.md).
WLAN, HTTP und Livebild funktionieren ohne SD. Laufzeitkomponenten liegen
unter `/opt/cam`, WLAN-Konfiguration unter `/data/wlan.conf`.

Der Webplayer bietet Start/Pause, Vollbild, Neuverbinden, Bildrate und
JPEG-Qualität; er löst keine Aufnahmen aus. `fps`: 1–25, `quality`: 20–90.
15 Bilder/s bleiben der Standard; 25 Bilder/s sind eine experimentelle
Obergrenze. Vor der Optimierung wurden bei JPEG-Qualität 65 etwa 11–12
Bilder/s gemessen. Die optimierte Aufnahme erreichte am 01.11.2026 mit
angeforderten 25 Bildern/s etwa 16–17 Bilder/s; bei der Einstellung 15 waren
es 14,8 Bilder/s. Ein längerer Durchlauf lieferte 300 gültige, unterschiedliche
JPEGs; die installierte Version wurde anschließend mit je 60 Bildern bei
beiden Einstellungen geprüft. Stabile 25 Bilder/s sind damit noch nicht erreicht.
Die Ausgabe zeigt die Display-Vorschau samt UI mit 320 × 240 Pixeln ohne Ton.
**Das Display muss angeschlossen sein**; ohne Display waren die JPEGs schwarz.

Die Videoeinstellung 1080p/30 oder 720p ändert diese Streamauflösung nicht.
Eine kleinere Aufnahmeauflösung könnte die Kamera indirekt entlasten;
ein Auflösungsvergleich wurde noch nicht gemessen. Hinzu kommen weiterhin
JPEG-Kodierung und Übertragung; die höhere Auswahl allein garantiert keine
entsprechende tatsächliche Bildrate.

## Optimierte Display-Aufnahme

Die feste Wartezeit von 55 ms wurde durch eine Abfrage markierter Zeilenränder
im eigenen ION-Puffer ersetzt. Das getestete ARGB-Writeback liefert deckende
Pixel; der Markierungswert kann daher von gültigen Bilddaten unterschieden
werden. Nach spätestens etwa 55 ms wird der Versuch beendet. Sind Zeilenränder
noch unverändert, folgt eine Wiederholung; bleibt auch diese unvollständig,
wird kein JPEG aus diesem Puffer ausgegeben. Die DMA-Aufnahme wird vor dem
Lesen und Freigeben weiterhin gestoppt. Pro Pixel wird ein ausgerichtetes
32-Bit-Wort statt dreier einzelner Bytes aus dem ungecachten Puffer gelesen.

Im Diagnosemodus wurde zusätzlich der **gesamte** Puffer vor jedem Bild
markiert und danach auf ungeschriebene Pixel geprüft: 307 Aufnahmen mit
adaptivem Warten ohne Fund. Ein bloßes Verkürzen auf 25 ms war dagegen bei
13 von 67 Aufnahmen unvollständig und wurde verworfen. Erzwungener vorzeitiger
Abbruch des ersten Versuchs prüfte die erfolgreiche Wiederholung; bei zwei
unvollständigen Versuchen antwortete der Server mit HTTP 503. Snapshot und
Stream bleiben über dieselbe Capture-Sperre koordiniert.

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

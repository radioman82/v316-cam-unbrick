# Allwinner V316 Cam Livevideo

**28.10.2026: Oberfläche auf Streaming reduziert.** Die Website bietet nur noch
Start/Pause, Vollbild, Neuverbinden sowie Bildrate (5/10/15 Bilder/s als Obergrenze)
und JPEG-Qualität (40/65/85). Beide Einstellungen werden je Browser gespeichert
und über `fps` und `quality` direkt an den Streamer übergeben. Der Streamer
akzeptiert 1–15 Bilder/s und Qualität 20–90; ungültige Parameter ergeben HTTP 400.
Die Auflösung bleibt 320 × 240. Die Website ruft keine Kamerasteuerung auf und
simuliert keine Tasten. Foto-/Video-Auslöser und Aufnahmearten wurden entfernt.
Die folgenden älteren Bedienungsnotizen dokumentieren den vorherigen Stand.

**Ergänzung vom 27.10.2026:** Der Player hat jetzt eine Kamerasteuerung mit
Moduswahl, Navigation, Auslöser und „Meldung schließen“. Dafür läuft die neue
Menü-Binary v22. Bedienung, Tests und Rückbau stehen in
[docs/WEBSTEUERUNG_UND_MODI_2026-10-27.md](../../docs/WEBSTEUERUNG_UND_MODI_2026-10-27.md).
Die folgenden Messungen beschreiben die erste Streaming-Installation.

Prüfung am 28.10.2026: Deployment mit `--streaming-only`, Sicherung unter
`/mnt/extsd/.stream-backup-20261028-095824-0b2a06`. 20/20 unterschiedliche,
dekodierbare JPEGs nach dem Aufspielen. Mit `fps=5&quality=40`: 12/12 Bilder
bei 5,0 FPS; mit `fps=10&quality=85`: 12/12 bei 7,1 FPS mit gleichzeitig
geöffnetem Browserstream. Einzelbilder mit Qualität 40/85 waren 5.921/10.923
Bytes groß, jeweils 320 × 240. Fünf ungültige Parameterabfragen wurden mit
HTTP 400 abgewiesen. Auswahl, Pause, Neuverbinden und Browser-Neuladen geprüft.

Auf der Kamera am **27.10.2026** installiert und geprüft:
[Webplayer](http://192.168.178.199:8080/),
[MJPEG-Stream](http://192.168.178.199:8080/cgi-bin/stream),
[JPEG-Einzelbild](http://192.168.178.199:8080/cgi-bin/snapshot).

Der Stream zeigt die laufende Display-Vorschau einschließlich UI und Meldungen,
im Querformat **320 × 240**, ohne Ton. Er ist kein Zugriff auf den hochauflösenden
Aufnahmestream. Eine einzelne Verbindung erreichte im Test rund **12 FPS**,
zwei gleichzeitige Verbindungen jeweils rund **7 FPS**. Das hängt auch von WLAN,
weiteren Clients und der Auslastung der Kamera ab.

## Ursache des Standbilds

Das bisherige Snapshot-CGI schrieb immer nach `/tmp/live.bmp`. Der Treiber
verweigert jedoch eine schon vorhandene Zieldatei. Im Kernel-Log wiederholte
sich `disp_capture_dump_store, open /tmp/live.bmp err`; drei HTTP-Abfragen
lieferten exakt denselben SHA256-Wert. Ein neuer Dateiname lieferte ein anderes
Bild. Weil das alte CGI nur die Existenz der Datei prüfte, blieb dieser Fehler
unbemerkt und das erste Bild wurde endlos wiederholt.

Das alte Stream-CGI hatte zusätzlich einen HTTP-Status im CGI-Header, eine
falsche Multipart-Boundary und BMP-Bilder statt JPEG. Der bisherige Webplayer
nutzte dieses CGI gar nicht, sondern lud wiederholt Einzelbilder.

Das Entfernen der alten Datei löst zwar das Einfrieren, aber der Diagnoseweg
`capture_dump` liefert auf diesem Gerät nur etwa ein Bild pro Sekunde. Die alte
Notiz `D:/v316cm/STATUS_STREAMING_ERFOLG.md` mit 10 ms Capturezeit war deshalb
keine belastbare Grundlage für flüssiges Video.

## Implementierung

- `v316cm_mjpeg.c`: kleines, statisch gelinktes ARMv7-Linux-Programm, JPEG-Qualität
  65, Zielrate höchstens 15 FPS; langsamere Clients erzeugen keinen Bildrückstau.
- `display_capture.h`: direkter Zugriff auf `/dev/disp` mit
  `DISP_CAPTURE_START`, `DISP_CAPTURE_COMMIT2`, `DISP_CAPTURE_STOP`. ION stellt
  einen eigenen, uncachebaren DMA-BUF bereit. Es werden keine fremden
  Kamerapuffer gelesen oder überschrieben. Drei Display-Refreshs werden vor
  dem Stop und dem Auslesen abgewartet (55 ms am gemessenen 58-Hz-Panel).
- Ein `flock` serialisiert die Hardwareaufnahme mehrerer Clients. Stop erfolgt
  vor dem Lesen/Freigeben des DMA-Puffers. JPEG-Kompression und Netzwerk laufen
  außerhalb der Hardware-Sperre. Schließt der Client, endet der Prozess;
  blockierte Schreibzugriffe haben ein Limit von zehn Sekunden.
- Falls sich der direkte Zugang nicht initialisieren lässt, bleibt der langsamere
  BMP-Diagnoseweg als Fallback. Er verwendet pro Prozess eine eigene Datei und
  entfernt sie vor jeder Aufnahme. Beschädigte/fehlende Bilder ergeben einen
  HTTP-Fehler statt eines alten Ersatzbilds. Ein Fehler im bereits initialisierten
  direkten Zugang beendet die betreffende Verbindung.
- `www/`: Webplayer mit einer dauerhaften MJPEG-Verbindung, Pause/Start,
  Vollbild, Einzelbild und Wiederverbindung bei einem Bildladefehler. Ein
  Hintergrund-Tab pausiert den Stream. Beide CGI-Skripte starten dieselbe Binary.

Es gibt keine neuen Python-, FFmpeg- oder Bibliotheksabhängigkeiten auf der
Kamera. Das Web-Deployment setzt nun die separat installierte Menü-Binary v22
für die Steuerung voraus. Es ergänzt `v316cm-control` und macht den vorhandenen
Streaming-Start bei bestehender Verbindung wiederholbar. WLAN-Konfiguration und
Boot-Hook werden nicht geändert. Der vorhandene HTTP-Server und die vorhandene
`cmd`-Schnittstelle werden weiterverwendet.

## Bauen und aufspielen

Auf dem PC: Python 3, für die Bildprüfung Pillow, zum Bauen **Zig 0.14.1**.
Die fertige ARM-Binary liegt bereits unter `firmware/streaming/v316cm-mjpeg`.

```powershell
python tools/streaming/build.py --zig D:\v316cm\.toolchains\zig-x86_64-windows-0.14.1\zig.exe
python -u tools/streaming/deploy.py --streaming-only --url http://192.168.178.199:8080
python -u tools/streaming/deploy.py --check --frames 60
```

`deploy.py` setzt die bereits auf dieser Kamera eingerichtete
`/cgi-bin/cmd`-Schnittstelle und `/mnt/extsd/bin/busybox` voraus. Es sichert
die bisherigen Dateien auf der SD-Karte, lädt in einen eigenen Staging-Ordner,
verifiziert jede Upload-Prüfsumme und prüft die neue Binary über ein temporäres
CGI. Erst nach mehreren unterschiedlichen, vollständig dekodierbaren JPEGs
werden Binary und Webdateien durch einzelne atomare Umbenennungen veröffentlicht.
Der anschließende Streamtest löst bei einem Fehler den Rückbau der Webdateien aus.
Die Umbenennungen bilden keine gemeinsame Transaktion; die Indexseite wird
zuletzt veröffentlicht. Ein Stromausfall während des Deployments wird nicht
automatisch rückgängig gemacht.

Alle Dateien bleiben auf der SD-Karte. Der vorhandene Startmechanismus für
WLAN und HTTP bleibt erhalten; ein Kaltstart wurde in dieser Sitzung nicht
ausgeführt.

`--streaming-only` veröffentlicht ausschließlich Streamer, Stream-/Snapshot-CGI
und Website. Kamerasteuerung, Menü-Binary und Streaming-Startskript werden dabei
nicht ersetzt; die vereinfachte Website benötigt die Menü-Erweiterungen nicht.

## Sicherung und Rückbau

Originalzustand vor der ersten Änderung dieser Sitzung:
`/mnt/extsd/.stream-backup-20261027-163415-159904`.
Die weiteren datierten Backups enthalten bereits Zwischenstände des neuen
Streamers. Der letzte enthält die vorherige Version mit direktem Capture.

Diese Befehle in der Kamera-Shell stellen die ursprünglichen Webdateien wieder her:

```sh
B=/mnt/extsd/.stream-backup-20261027-163415-159904
cp "$B/index.html" /mnt/extsd/www/index.html
cp "$B/cgi-bin/stream" /mnt/extsd/www/cgi-bin/stream
cp "$B/cgi-bin/snapshot" /mnt/extsd/www/cgi-bin/snapshot
sync
```

Anschließend die Browserseite neu laden. Die zusätzliche Binary wird dann nicht
mehr verwendet und kann später entfernt werden. Es ist kein Firmware-Rückflash
erforderlich.

## Verifikation am Gerät

- Ein Stream: **60/60 unterschiedliche, dekodierbare JPEGs**, **320 × 240**,
  **12,2 FPS**, zuletzt **13.696 Bytes/Bild** statt vorher **307.254 Bytes/BMP**.
- Zwei parallele Streams plus Einzelbildabrufe: jeweils **24/24 unterschiedliche
  JPEGs**, **7,5 bzw. 7,1 FPS**. Einzelbilder hatten korrekte Länge und Abmessungen.
- Nach dem Schließen waren keine Streamer-Prozesse mehr vorhanden; kein
  temporäres Capture-Bild blieb liegen. Freier Speicher kehrte ungefähr zum
  Ausgangswert zurück (11,8 MB frei, etwa 22,6 MB inklusive Cache verfügbar).
- Webplayer im Browser geprüft, einschließlich Pause/Start und Querformat.
- Menü-Binary bei der ersten Streaming-Installation: MD5 `4154e8520e13711bc70fe9e65d424ec7`
  für `/usr/bin/sdvcam` und `/mnt/extsd/sdvcam`. Die neueren Menü-Arbeiten
  außerhalb dieses Repositories wurden nicht mit diesem Streaming-Fix importiert.

## Quellen / Abhängigkeiten

Die ABI-Deklarationen orientieren sich an den veröffentlichten Allwinner-Quellen;
ihre Funktion wurde auf der vorhandenen Allwinner V316 Cam geprüft:

- [Allwinner disp2 ABI](https://github.com/Allwinner-Homlet/H6-BSP4.9-linux/blob/master/include/video/sunxi_display2.h)
- [Allwinner Display-IOCTLs](https://github.com/Allwinner-Homlet/H6-BSP4.9-linux/blob/master/drivers/video/fbdev/sunxi/disp2/disp/dev_disp.c)
- [Allwinner Capture-Implementierung](https://github.com/Allwinner-Homlet/H6-BSP4.9-linux/blob/master/drivers/video/fbdev/sunxi/disp2/disp/de/disp_capture.c)
- [Legacy ION ABI](https://github.com/Allwinner-Homlet/H6-BSP4.9-linux/blob/master/drivers/staging/android/uapi/ion.h)
- [stb_image_write](https://github.com/nothings/stb/blob/1ee679ca2ef753a528db5ba6801e1067b40481b8/stb_image_write.h),
  Version 1.16, MIT oder Public Domain; Original samt Lizenz in `vendor/`,
  Quelle und SHA256 in `vendor/SOURCE.txt`.
- [Zig Download](https://ziglang.org/download/), Build mit `arm-linux-musleabihf`,
  Cortex-A7 und statischer musl. Der Compiler liegt außerhalb des Repositories.
> Aktueller Stand vom 28.10.2026: [Übersicht und Installationsweg](../../docs/AKTUELLER_STAND_2026-10-28.md).
> Die IPC-Steuerung ist experimentell und nicht aktiv. Für die aktuelle Kamera
> nur `deploy.py --streaming-only` und den separaten UI-Installer verwenden.

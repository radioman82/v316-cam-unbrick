# Websteuerung und Aufnahmearten — 27.10.2026

Installiert auf der angeschlossenen V316CM. Weboberfläche:
<http://192.168.178.199:8080/>. Falls noch die alte Seite erscheint: neu laden.
Die Bedienung nutzt horizontale Button-Reihen und nebeneinanderliegende Foto-/
Video-Gruppen. Ab 1000 Pixel Fensterbreite steht die Steuerung neben dem Livebild;
auf schmalen Fenstern werden die Reihen umgebrochen.

## Bedienung

- **Meldung schließen:** quittiert die nichtmodale Kamerameldung, ohne den
  Auslöser zu betätigen. Bei geöffneten Auswahlfenstern wird vorher in die
  Vorschau zurückgekehrt. Die ursprüngliche 30%-Akkumeldung ließ sich während
  dieser Änderung nicht erneut beobachten; der Hide-Aufruf für das anhand des
  Battery-Low-Handlers identifizierte Prompt-Fenster ist eingebaut. Ein erneuter
  Test mit genau dieser Meldung ist noch offen.
- **FOTO · Modi:** öffnet Foto, Auto, Serie und Timer.
- **VIDEO · Modi / STREAM · Modi:** öffnen Video, Zeitlupe, Loop und Zeitraffer.
- Die acht einzelnen Aufnahmeart-Buttons wählen den Modus direkt; sie lösen
  noch keine Aufnahme aus. Der Sensorwechsel kann einige Sekunden dauern.
- **Auslöser · Foto / Video:** nimmt ein Foto auf oder startet/stoppt die
  Videoaufnahme. Bei einer laufenden Videoaufnahme zeigt der Button
  **Videoaufnahme stoppen**. Der Kamerastatus wird regelmäßig abgefragt.
- **▲ / ▼ / OK:** bedienen das sichtbare Kameramenü.
- **Zurück / Vordertaste:** entspricht einem kurzen Druck auf die Vordertaste.
  In den Einstellungen durchläuft diese Taste Video/Foto → Gerät → Zurück.
- **4 Kacheln**, **Aufnahmearten**, **Einstellungen** öffnen die jeweilige Ansicht.
- **Web-Snapshot** öffnet nur ein JPEG der Display-Vorschau. Er löst kein
  hochauflösendes Foto auf der SD-Karte aus.

Auch die Hardware ist angepasst: Die Seitentasten öffnen in der Vorschau die
Aufnahmearten. Die Vordertaste öffnet/schließt die Kacheln; bei geöffneten
Aufnahmearten schließt sie die Auswahl. Die obere OK-Taste bleibt der Auslöser
beziehungsweise bestätigt den markierten Menüeintrag. Sie ist kein verlässlicher
Schließen-Knopf für die nichtmodale Akkumeldung.

## Technischer Stand

**Menü-Binary v22, MD5 `ece022b21206d5bc28058b24cf3790d7`.**
Der Builder reproduziert zunächst v21 exakt aus der Repository-Basis `sdvcam_v8`
und prüft dessen MD5 `4154e8520e13711bc70fe9e65d424ec7`. Danach folgen nur
bytegeprüfte Änderungen. Build:

```powershell
python tools/build_menu_v22.py
python tools/streaming/build.py --zig D:\v316cm\.toolchains\zig-x86_64-windows-0.14.1\zig.exe
python -u tools/deploy_menu_v22.py
python -u tools/streaming/deploy.py
```

Der Menü-Builder verwendet den bereits vorhandenen Arm-GNU-Assembler unter
`C:/Program Files (x86)/Arm GNU Toolchain arm-none-eabi/13.3 rel1/bin`.

Die Kacheln setzen die Familie und erneuern die vorhandene Modusliste. Die
Listenansicht erhält jeweils vier der acht ursprünglichen Einträge; die temporär
angepassten Vektorzeiger werden vor dem Freigeben wiederhergestellt. Der
Foto-Callback übersetzt die lokalen Indizes 0–3 zurück auf die ursprünglichen
Modi 4–7. Die neue Familie liegt im bisher ungenutzten Padding-Byte `+0x11d`
des ModelSelectWindow. Die ursprünglichen Callback-Sprungziele bleiben intakt.

Zusatzcode liegt im ersetzten Dispatcher-Slot und im bytegeprüften freien
Bereich `0x24ad84..0x24ae6c` unmittelbar neben dem vorhandenen Menü-Stub. Die
Binärgröße bleibt 3.407.624 Bytes. Die Dateien `/mnt/extsd/sdvcam` und
`/mnt/extsd/.sdvcam_patched` enthalten denselben Stand; letzterer wird durch den
vorhandenen Boot-Hook eingebunden. Es wurden keine Flash-Partitionen verändert.

`v316cm-control` ergänzt den MJPEG-Streamer. Das neue `/cgi-bin/control` bietet
GET für Status und POST für eine feste Liste von Aktionen. Es führt keine
übergebenen Shellbefehle aus. Fremde Browser-Origins werden abgewiesen.
Tastendrücke sind auf 20 ms begrenzt, Aktionen werden mit `flock` serialisiert.
Der Helfer liest den geprüften UI-Zustand über `/proc/<pid>/mem`, schreibt dort
aber nicht. Er verweigert die Steuerung bei einer anderen Menü-/Speicherstruktur.

Aufnahmen werden anhand der vom Kameraprozess zum Schreiben geöffneten
DCIM-Videodateien erkannt. Das zunächst untersuchte Preview-Feld `+0x160` ist
hierfür ungeeignet. Moduswechsel über die Websteuerung werden während einer
laufenden Aufnahme blockiert. Der Auslöser bleibt zum Stoppen verfügbar.

Der Streaming-Start beendet sich bei bereits bestehender WLAN-Verbindung und
einem Listener auf dem konfigurierten HTTP-Port, statt die Verbindung neu
aufzubauen. Das ist insbesondere bei Bedienung der STREAM-Kachel aus dem Browser
notwendig. SSID, Passwort, IP-Konfiguration und der bestehende Boot-Hook bleiben
erhalten.

## Geprüft am Gerät

- COM11 bei 115200 Baud: Zu Sitzungsbeginn wurde eine Linux-Shellantwort mit CR
  als Zeilenende empfangen. Später kam dort nur noch ein Echo an; die Ursache
  ist offen. Deployment, Steuerung und Abschlussprüfungen erfolgten über WLAN.
- Alle acht Aufnahmearten wurden einzeln über HTTP gewählt und im App-Log mit
  den tatsächlichen Status-/Backend-Modi **0 bis 7** bestätigt.
- Getrennte Foto- und Videoauswahl im Display-Capture visuell kontrolliert.
- Kacheln öffnen/schließen, Aufnahmearten öffnen/schließen und direkte
  Modusauswahl geprüft. Eine nach dem Start gespeicherte Foto-Aufnahmeart wird
  beim ersten Öffnen der Auswahl in die Foto-Gruppe übersetzt.
- Videoaufnahme über HTTP gestartet, laufende Aufnahme erkannt, Foto-Moduswechsel
  mit HTTP 409 abgewiesen, Aufnahme wieder gestoppt. Dabei wurden Testclips auf
  der SD-Karte angelegt und dort belassen.
- STREAM wiederholt gewählt: WLAN-Prozess und TCP-Listener blieben erhalten;
  das Log bestätigt `WLAN and HTTP already running - keeping current connection`.
- POST von fremdem Origin ergibt HTTP 403; unbekannte Aktion `reboot` ergibt
  HTTP 409 ohne Ausführung.
- Browser zeigt die Bedienelemente und aktualisiert den tatsächlichen
  Kamerazustand. „Meldung schließen“ beendet die Auswahl und löst keine Aufnahme
  aus; der erneute Test mit aktiver 30%-Akkumeldung steht noch aus.
- Livevideo bleibt aktiv. Ein vollständiger Kaltstart ist noch nicht geprüft.

## Sicherungen und Rückbau

Der ursprüngliche Menüstand v21 liegt weiterhin hier:
`/mnt/extsd/.control-backup-20261027-170422/sdvcam_v21`.
Die weiteren `.control-backup-*`-Ordner enthalten die getesteten Zwischenstände.
Vorherige Webdateien und das ursprüngliche Streaming-Startskript liegen unter
`/mnt/extsd/.stream-backup-20261027-171023-1c4a5c`.

Zum Rückbau zuerst die Aufnahme stoppen und den Kameraprozess beenden. Dann
die v21-Sicherung sowohl nach `/mnt/extsd/sdvcam` als auch nach
`/mnt/extsd/.sdvcam_patched` zurückkopieren, synchronisieren und die Kamera neu
starten. Für die Weboberfläche `index.html`, `cgi-bin/stream`,
`cgi-bin/snapshot` und `start_streaming.sh` aus der genannten Websicherung
wiederherstellen. `cgi-bin/control` und die zusätzliche Steuerungs-Binary werden
von der alten Seite nicht verwendet. Ein Firmware-Rückflash ist nicht nötig.

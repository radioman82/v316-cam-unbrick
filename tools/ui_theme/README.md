# Allwinner V316 Cam – einheitliche Kamera-Menüs, v23

Stand: 28.10.2026. Umsetzung des freigegebenen Entwurfs für das
320 × 240-Display. Die Streaming-Website bleibt unverändert.

## Startansicht und SD-Abgleich vom 29.10.2026

Aktuelle App: MD5 `4614a61766519e17a778c914956c8ff9`. Das Vier-Kachelmenü
öffnet beim Booten automatisch, ohne Tastendruck oder simuliertes Eingabeereignis.
Der Hook wartet auf den zweiten `OnWindowLoaded`-Aufruf, nachdem die
Kachelressourcen geladen sind, und ruft das vorhandene Menüfenster direkt auf.
App-Neustart und vollständiger Neustart wurden am Gerät geprüft: Die App läuft,
das Menü ist sichtbar und der Framebuffer bleibt statisch. Vor dem Menü ist
noch kurz die Videovorschau zu sehen. Das Überspringen des ersten nativen
Fensteraufrufs und ein schwarzer Überzug verhinderten auch die sichtbare
Menüanzeige; beide Versuche wurden zurückgenommen.

```powershell
python tools/ui_theme/build.py
python tools/ui_theme/deploy_startup.py
```

Der schlanke Installer setzt den vorherigen v23-Stand mit MD5
`211d51fe21a397c73ea6a3ce8f6a0e13` voraus, sichert die SD-App und
überträgt nur geänderte Binärbereiche. Die installierten SD-Skripte für
STREAM wurden zusätzlich auf die von der App verwendeten
`/tmp/v316cm-*`-Marker abgeglichen. Ein älteres SD-Backup mit den bisherigen
Marker-Namen würde WLAN beim STREAM-Wechsel sofort wieder beenden.

## Umfang und Bestandsaufnahme

Alle 33 vorhandenen `.ui`-Vorlagen und die zugehörigen Ressourcen wurden
eingelesen. Neben Setup und seinen Wertelisten existieren eigene Klassen für
Datum/Uhrzeit, Informationen, Hinweise, Bestätigungen, WLAN-Informationen,
USB-Auswahl, Wiedergabelisten, Sprachbefehle und das Schnellmenü.

- Setup: drei horizontale Reiter, breite Karten, Bezeichnung und Wert
  untereinander, vier Einträge je Seite und Positionsanzeige.
- Untermenüs: eigene Überschrift, einheitliche Karten und Unterscheidung
  zwischen Fokusrahmen und gespeichertem Wert (`Aktiv`).
- Datum/Uhrzeit: passende Kopfzeile, ausreichend breiter Fertig-Button,
  einheitliche Pfeile und zweistellige Zeitfelder.
- Informationen, Hinweise und Bestätigungen: gemeinsame Farben,
  pixelgenau gemessener Zeilenumbruch, passende Abstände und abgerundete
  Schaltflächen. Der Formatierdialog erläutert den Datenverlust.
- Weitere Listen verwenden denselben zentralen Renderer; die Ressourcen für
  Wiedergabeliste, Sprachbefehle, USB-Auswahl und Medienliste sind angepasst.
- Bildbasierte Bedienelemente des alten Schnellmenüs sowie Trennlinien und
  Auswahlmarkierungen haben passende dunkle/goldene Varianten erhalten.
- Deutsche Bezeichnungen und Meldungen wurden korrigiert. Beispiele:
  Belichtungskorrektur statt Auflösungseinstellungen, Bildschirm aus,
  Automatisch aus, Tastentöne, Bildformat, kurze Ein-/Aus-Werte.

Das bereits gestaltete Vier-Kachel-Menü und die Aufnahmeart-Kacheln bleiben
erhalten. Vorschau, Video-Wiedergabe, Statusleiste und Bildschirmschoner werden
nicht vom Listen-/Dialog-Renderer überzeichnet. Die Ressourcen enthalten auch
unbenutzte IPC-/Launcher-/Wizard-Vorlagen für andere Geräte, darunter einen
1280 × 800-Assistenten; diese werden auf der Allwinner V316 Cam nicht aktiviert.

## Technik

Basis ist ausschließlich `sdvcam_menu_v22`, MD5
`ece022b21206d5bc28058b24cf3790d7`. Der Builder prüft jede ersetzte Stelle.
Ein zusätzliches RX-ELF-Segment enthält den kleinen Renderer und den
Glyphenatlas; die ursprünglichen Code-/Datenadressen bleiben erhalten.
Es werden keine Bibliotheken vorab geladen und keine neuen Dienste gestartet.

### Trennung von Kamera und Streaming

Die PHOTO-/VIDEO-Kacheln löschen den flüchtigen Streaming-Zustand und beenden
WLAN, HTTP, Telnet und laufende MJPEG-Verbindungen. Die WLAN-Module werden
entladen. STREAM verwendet die native Videovorschau, öffnet keine Aufnahmeart-
Auswahl und kennzeichnet sie mit `LIVE` sowie `Streaming`. Die Aufnahmebefehle
59/62/81 und die kurze OK-Taste in der Vorschau werden in diesem Zustand
abgefangen. Menübestätigungen und langes OK behalten ihre native Funktion.
Ein Wechsel während einer laufenden Aufnahme wird über die geöffneten,
schreibbaren Mediendateien verhindert.

`/tmp/v316cm-stream-mode` enthält den gewünschten Zustand; der serialisierte
Worker `network_mode.sh` gleicht ihn auch bei schnellen Kachelwechseln ab.
`start_streaming.sh` bricht verwaltete Starts ab, sobald Video/Foto gewählt
wurde. Die beiden weiteren Skripte werden mit gesichert und installiert.
Beim Neustart ist der flüchtige Zustand gelöscht. Die Weboberfläche bleibt
auf Streaming beschränkt.

Am Gerät geprüft: Video und Foto beenden WLAN einschließlich Entladen der
xradio-Module. STREAM stellt die Verbindung wieder her und liefert 12
unterschiedliche JPEGs bei etwa 12 FPS. Der direkte Aufruf der gesperrten
Auslösepfade startet keine Aufnahme; der Medienbestand bleibt gleich.
Die Einstellungsdatei bleibt beim vollständigen Video/Foto/Stream-Wechsel
bytegleich. Das vor dem Startpatch installierte Image hatte MD5
`211d51fe21a397c73ea6a3ce8f6a0e13`; Sicherung des vorherigen Stands:
`/mnt/extsd/.ui-theme-backup-20261028-115215`.

Die OK-Sperre liest ausschließlich die Sichtbarkeitsfelder der vorhandenen
Menüfenster. Die Firmware-Funktion bei `0x5a658` schließt offene Fenster und
darf dafür nicht verwendet werden: Sie hätte beim Wechsel aus Streaming die
Kachelwahl vor der nativen OK-Verarbeitung verworfen. Die Geräteprüfung führt
deshalb zusätzlich den echten OK-Handler mit sichtbar ausgewählter Video-
bzw. Foto-Kachel aus, statt nur den Ziel-Callback direkt zu prüfen.

Die Paint-Handler für QTableView/ListView, QListView/MenuItems, Text,
Grafik-/Schaltflächen und Fensterhintergründe sind zentral angepasst.
Die Originalhandler verarbeiten weiterhin alle anderen Nachrichten,
insbesondere die Kameratasten und die Einstellungs-Callbacks. Beschriftungen
werden anhand der tatsächlich gerenderten Glyphenbreite umgebrochen.

Die Wartungsdatei `/tmp/v316cm-ui-command` erlaubt der Geräteprüfung, auf dem
GUI-Thread die nativen Menüfunktionen aufzurufen. Die Website verwendet sie
nicht. Es werden keine Eingabeereignisse oder Tastensequenzen erzeugt.
Insbesondere muss Setup über die native App-Nachricht geöffnet werden:
Ein bloßer Fensterwechsel lädt den Einstellungs-Presenter nicht vollständig
und würde Standardwerte anzeigen. Befehle atomar über eine temporäre Datei
und anschließendes Umbenennen bereitstellen.

ABI-Abgleich mit den offiziellen
[MiniGUI-ListView-Deklarationen](https://github.com/VincentWei/minigui/blob/rel-3-0/include/ctrl/listview.h),
[Fensternachrichten](https://github.com/VincentWei/minigui/blob/rel-3-0/include/window.h)
und [GDI-Deklarationen](https://github.com/VincentWei/minigui/blob/rel-3-0/include/gdi.h).
Die konkreten Erweiterungen und Objektfelder wurden gegen die vorhandene
Firmware und die Darstellung am Gerät geprüft.

## Reproduktion und Installation

Voraussetzungen: Python mit Pillow, Windows-Schrift Segoe UI und die bereits
verwendete Arm GNU Toolchain 13.3. Der Builder erzeugt den Glyphenatlas lokal;
eine vollständige Schriftdatei wird nicht auf die Kamera kopiert.

```powershell
python tools/ui_theme/build.py
python -u tools/ui_theme/deploy.py
```

Ausgaben unter `firmware/ui_theme/`: Kamera-App, Layouts, deutsche Texte,
Bildressourcen und Manifest. `installed.json` beschreibt die letzte lokale
Installation; es gehört nicht zur reproduzierbaren Firmware.

Das Deployment sichert App, Layouts, Sprachdatei, Bilder und Boot-Hook auf
der SD-Karte, prüft Upload-Prüfsummen, startet die App neu und prüft Prozess
und JPEG-Ausgabe. Bei einem Fehler stellt es den vorherigen Stand wieder her.
Der Boot-Hook bindet die Ressourcen nur ein, wenn die Prüfsumme der SD-App
zur Aktivierungsdatei passt. Die Änderungen schreiben keine Firmware-Partition.

## Geräteprüfung

24 Ansichten geprüft: Geräteliste, Netzfrequenz, Bildschirmabschaltung,
automatisches Ausschalten, Tastentöne, Sprache, Datumsformat, Uhrzeit, Datum,
Formatierdialog, Geräteinformationen, Rücksetzdialog, Video-Einstellungsliste,
Videoauflösung, Weißabgleich, Belichtung, Messmodus, Schärfe, Qualität und ISO
sowie Foto-Einstellungsliste, Fotoauflösung, Foto-Weißabgleich und Verschlusszeit.

Formatieren und Zurücksetzen wurden jeweils nur geöffnet und abgebrochen.
Es wurde keine Aufnahme ausgelöst. Nach dem Fotomenü-Test wurde der
ursprüngliche Videomodus wiederhergestellt. `/data/setting.lua` und
`/tmp/data/setting.lua` hatten vor und nach dem Durchlauf dieselbe MD5:
`d101d37818e0435fe7352cb208375598`.
Anschließend lieferte der Stream 12 unterschiedliche, vollständig dekodierbare
JPEGs bei eingestellten 5 FPS. Die selteneren USB-, Sprachbefehls-, Wiedergabe-
und Schnellmenüvarianten wurden anhand ihrer gemeinsamen Renderer und
Ressourcen geprüft, nicht durch Auslösen der jeweiligen Hardwarefunktionen.

Ein Startabbruch im Zwischenstand wurde auf das Abfragen anderer
Einstellungsfenster während des Dialogaufbaus eingegrenzt. Dialogüberschriften
werden jetzt aus der eigenen Dialoginstanz ermittelt; die geprüften
Nachfolgestände liefen stabil. Ein vollständiger Kaltstart ist nicht Teil
dieses Testprotokolls.

## Rückbau auf den Ausgangsstand vor dem Theme

Vollständige erste Sicherung:
`/mnt/extsd/.ui-theme-backup-20261028-102620`.
Die nachfolgenden Sicherungen enthalten Zwischenstände des Themes.

In der Kamera-Shell, bei gestoppter Aufnahme:

```sh
B=/mnt/extsd/.ui-theme-backup-20261028-102620
killall sdvcam
sleep 1
if pidof sdvcam >/dev/null; then killall -9 sdvcam; fi
umount /usr/share/minigui/res/layout
umount /usr/share/minigui/res/lang/zh-DE.xml
umount /usr/share/minigui/res/images
mv /mnt/extsd/custom_ui /mnt/extsd/ui_theme/images-before-rollback
cp -r "$B/images" /mnt/extsd/custom_ui
mount --bind /mnt/extsd/custom_ui /usr/share/minigui/res/images
cat "$B/sdvcam_previous" > /mnt/extsd/sdvcam
cat "$B/boot_binary" > /mnt/extsd/.sdvcam_patched
cat "$B/S00zsdvcam" > /etc/init.d/S00zsdvcam
umount /usr/bin/sdvcam
mount --bind /mnt/extsd/.sdvcam_patched /usr/bin/sdvcam
sync
FB_SYNC=1 SCREEN_INFO=240x376-32bpp LD_HWCAP_MASK=0x00000000 /usr/bin/sdvcam >/tmp/sdvcam.log 2>&1 </dev/null &
```

Der Sicherungsname `images-before-rollback` darf dabei noch nicht existieren.
Die bisherigen Theme-Bilder bleiben dort für einen späteren Vergleich erhalten.

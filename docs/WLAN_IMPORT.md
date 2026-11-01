# Einmaliger WLAN-Import von SD

**Entwicklungsstand 01.11.2026:** Implementiert, aber noch nicht vollständig
am Gerät geprüft. Der automatische Import ist auf der Kamera deaktiviert.
Das bisherige WLAN funktioniert mit dem neuen, datenbasierten Konfigurationsweg
weiterhin. Displaybestätigung, DHCP-Import, Rückfall bei einem Verbindungsfehler
und anschließendes Löschen der SD-Datei stehen als Gerätetests noch aus.

## Vorgesehene Bedienung

1. [Beispieldatei](../tools/wlan_import/wlan.conf.example) mit den eigenen
   Daten als `wlan.conf` ins Hauptverzeichnis der SD-Karte kopieren.
2. Kamera starten. Nach der Geräteinitialisierung erscheint die Abfrage;
   ein vorhandenes Firmwareupdate hat Vorrang. Während einer Videoaufnahme
   wird kein Import gestartet.
3. Erst bei sichtbarer Abfrage OK/Auslöser zwei Sekunden halten.
   Andere Tasten oder 30 Sekunden ohne Bestätigung brechen ab.
4. Die Kamera prüft WLAN-Anmeldung und IP-Zuweisung. Internetzugang ist
   nicht erforderlich. Bei DHCP erscheint die zugewiesene IP-Adresse.
5. Erst nach erfolgreichem Verbindungstest werden die neuen Daten intern
   gespeichert. Danach wird die unveränderte ursprüngliche SD-Datei gelöscht.
   Wurde sie zwischenzeitlich bearbeitet, entfernt oder ist die SD nicht
   beschreibbar, bleibt sie erhalten beziehungsweise muss selbst gelöscht werden.

Bei einem Fehler bleiben bisherige Einstellungen und die SD-Datei erhalten.
Die Kamera versucht, die vorherige Verbindung wiederherzustellen. Ein
Schreibfehler beim Speichern darf nicht zum Löschen der SD-Datei führen.
Die aktuelle Implementierung muss diese Abläufe noch am Gerät nachweisen.

## Dateiformat

UTF-8 mit oder ohne BOM; Windows- und Unix-Zeilenenden werden angenommen:

```ini
ssid=Mein WLAN
password=Mein Passwort
ip_mode=dhcp
```

Alles nach `=` ist der Wert, einschließlich Leerzeichen, `#`, Anführungszeichen
oder Backslashes. Keine zusätzlichen Anführungszeichen um Werte setzen.
WLAN-Namen dürfen bis zu 32 UTF-8-Bytes haben. Passwörter benötigen 8–63 Bytes;
alternativ wird ein bestehender 64-stelliger Hex-PSK angenommen. Unterstützt
wird der bereits vorhandene WPA-PSK-Verbindungsweg, kein neues WPA3-Verfahren.

Optional ist eine feste IPv4-Konfiguration möglich:

```ini
ssid=Mein WLAN
password=Mein Passwort
ip_mode=static
address=192.168.1.42
netmask=255.255.255.0
gateway=192.168.1.1
http_port=8080
```

Ohne Portangabe gilt 8080. Die tatsächliche Netzadresse muss zum eigenen
Router passen. Für eine gleichbleibende Adresse bei DHCP eignet sich eine
Adressreservierung im Router.

Die bisherigen Schlüssel `ROUTER_SSID`, `ROUTER_PASS`, `CAM_IP`, `NETMASK`,
`GATEWAY` und `STREAM_PORT` werden ebenfalls als Daten gelesen; einfache
umgebende Anführungszeichen werden dabei entfernt. Es findet keine
Shellauswertung statt. Doppelte oder unbekannte Schlüssel, Steuerzeichen,
ungültiges UTF-8 und übergroße Dateien werden abgewiesen.

## Speicherung und Verbindung

- Persistente Konfiguration: `/data/wlan.conf`, atomar ersetzt, Modus 0600.
- Kandidat und Rückfallsicherung: eigenes privates RAM-Verzeichnis.
- WLAN-Laufzeitdaten: `/run/v316-wlan/`, ebenfalls nur für root zugänglich.
- SSID und PSK werden hexadezimal an wpa_supplicant übergeben. Die PSK-
  Ableitung nutzt Zig-Standardbibliothek PBKDF2-HMAC-SHA1; Zugangsdaten werden
  nicht in Shellbefehle oder ungeschützte Konfigurationsstrings eingesetzt.
- Die SD-Datei wird als begrenzte reguläre Datei ohne Symlinkverfolgung gelesen.
  Vor dem Löschen werden Dateiidentität und vollständiger Inhalt erneut geprüft.
- Neue Image-Builds enthalten eine leere WLAN-Vorlage statt persönlicher
  Routerdaten. Die Installation migriert vorhandene Daten vorher ins interne
  Overlay, das der SD-Updater erhält.

Das Löschen einer Datei auf Flashmedien ist keine garantierte sichere Löschung.
Persönliche Konfigurationen, Testprotokolle und gerätespezifische Sicherungen
gehören nicht ins öffentliche Repository.

## Bauen und bisherige Prüfung

```powershell
python tools/wlan_import/build.py --zig PATH/TO/zig.exe --output ../internal-image-build/wlan-import/wlan-import
python tools/wlan_import/build.py --zig PATH/TO/zig.exe --output ../wlan-tests/parser.exe --host-test
python tools/wlan_import/test_config.py ../wlan-tests/parser.exe
```

Sechs Testgruppen bestehen: literal erhaltene Sonderzeichen, UTF-8-/Längen-
grenzen, Legacy-/CRLF-/BOM-Dateien, ungültige Eingaben und PSK-Vergleich mit
Python `hashlib.pbkdf2_hmac`. Die vorhandene reale statische WLAN-Verbindung
wurde anschließend über den neuen Parser und die abgeleitete PSK erfolgreich
neu aufgebaut. Die interne Konfiguration ist Modus 0600.

Installation mit neuer privater Sicherung, ohne einen Import zu starten:

```powershell
python tools/wlan_import/deploy.py --binary ../internal-image-build/wlan-import/wlan-import --backup ../wlan-backup-NEU
```

Der Boot-Hook wird dabei absichtlich noch nicht aktiviert. Nach abgeschlossenen
Gerätetests ermöglichen `--enable-boot` beim Installer und `--enable-wlan-import`
beim internen Image-Builder die automatische Startabfrage. Manuelle Prüfung
über die UART-Shell: `/opt/cam/wlan/wlan-import --import /mnt/extsd/wlan.conf /data/wlan.conf`.
Auch dieser Aufruf benötigt die Bestätigung auf der Kamera.

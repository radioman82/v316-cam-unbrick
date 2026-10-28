# Allwinner V316 Cam – aktueller Stand am 28.10.2026

Installiert und auf der Kamera geprüft: Menü v23, MD5
`211d51fe21a397c73ea6a3ce8f6a0e13`.

- Vier Kacheln: Foto, Video, Streaming und Setup.
- Foto/Video schalten beim Bestätigen der Kachel Streaming, WLAN, HTTP und
  Telnet ab; die WLAN-Module werden entladen.
- Streaming startet WLAN und MJPEG mit eigener LIVE-Anzeige. Kurzes OK in
  der Vorschau und native Aufnahmebefehle lösen dort keine Aufnahme aus.
  Die OK-Auswahl in Menüs bleibt möglich.
- Setup und weitere Menü-/Dialogansichten sind im dunklen Kachelstil
  überarbeitet; deutsche Texte und Umbrüche sind angepasst.
- Die Website enthält ausschließlich Streaming-Einstellungen, Pause/Start,
  Vollbild und Neuverbinden. Keine Foto-/Video-Auslöser.
- MJPEG: 320 × 240, ohne Audio, zuletzt 12 unterschiedliche Bilder bei etwa
  12 FPS geprüft. Beim Wechsel zu Foto/Video wird die Website unerreichbar,
  weil WLAN dabei ausgeschaltet wird.

## Reproduktion und Installation

Details: [UI und Modus-Trennung](../tools/ui_theme/README.md),
[MJPEG-Streaming](../tools/streaming/README.md).

```powershell
python tools/build_menu_v22.py
python tools/ui_theme/build.py
python -u tools/ui_theme/deploy.py
python -u tools/streaming/deploy.py --streaming-only
python tools/streaming/deploy.py --check --frames 12
```

Zum Aufspielen STREAM an der Kamera aktivieren. Die aktuelle Webadresse ist
`http://192.168.178.199:8080/`; die serielle Root-Shell ist über COM11 mit
115200 Baud erreichbar. WLAN-Zugangsdaten bleiben auf der SD-Karte und
gehören nicht ins Repository.

Der UI-Installer installiert auch `start_streaming.sh`, `stop_streaming.sh`
und `network_mode.sh`. Der Boot-Hook lädt die geprüfte SD-App und ihre
Ressourcen automatisch. Es wurden keine Firmware-Partitionen geschrieben.
Letzte Sicherung auf der SD-Karte:
`/mnt/extsd/.ui-theme-backup-20261028-115215`.

## Prüfungen und letzter behobener Fehler

Video und Foto wurden über den OK-Handler mit markierter Kachel geprüft:
Streaming-Zustand gelöscht, WLAN aus, passendes Modussymbol. Rückkehr zu
STREAM und gesperrte Auslösebefehle wurden ebenfalls geprüft. Zusätzlich
wurden schnelle Moduswechsel und die Freigabe der Netzwerksperre geprüft.

Die erste OK-Sperre rief versehentlich die Firmware-Funktion `0x5a658` zum
Abfragen des Menüstatus auf. Diese Funktion schließt jedoch offene Menüs.
Die korrigierte Version liest ausschließlich deren Sichtbarkeit und lässt
die native Auswahlverarbeitung laufen. Direkte Tests nur des Ziel-Callbacks
hatten diesen Fehler zunächst nicht erfasst.

## Historische und experimentelle Bestandteile

[Websteuerung vom 27.10.](WEBSTEUERUNG_UND_MODI_2026-10-27.md) dokumentiert
den früheren Stand. Seine Web-Auslöser gehören nicht mehr zur aktuellen UI.

`v316cm_direct.c`, `libv316cm-direct.so` und die zugehörige IPC-Variante von
`v316cm-control` sind ein nicht aktivierter Entwicklungsstand. Der Loader-
Ansatz war auf dem Gerät nicht erfolgreich. Sie werden zur Sicherung der
Arbeit mit versioniert, sind aber für die aktuelle Oberfläche nicht nötig.
Den allgemeinen Streaming-Installer ohne `--streaming-only` deshalb nicht
für diesen Kamerastand verwenden. Die aktuelle direkte Menünavigation läuft
im GUI-Thread über die geprüfte App-Erweiterung, ohne Eingabeereignisse.

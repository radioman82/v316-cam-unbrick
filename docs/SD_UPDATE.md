# Firmware-Update von SD

**Entwicklungsstand vom 31.10.2026: noch nicht für reguläre Updates freigegeben.**
Paket-/Hardwareprüfungen, Ablehnung fehlerhafter Pakete und der echte Wechsel
von Init in die RAM-Umgebung mit ausgehängten Flash-Dateisystemen und Neustart
sind auf der Kamera geprüft. **Ein tatsächliches SD-Flashen und die anschließende
Rückleseprüfung sind noch offen.** Die Display-/Tastenabfrage muss nach einer
Korrektur des `EVIOCGKEY`-Rückgabewerts erneut getestet werden; ebenso der
verzögerte Start in eigener Session. Der vorläufige Start-Hook wurde zum
Sitzungsende entfernt, die SD ist wieder eine reine Medienkarte. FEL bleibt
bis zum abgeschlossenen Gerätetest der vollständig geprüfte Installationsweg.

Der Updater gehört in den internen Flash. Auf einer normalen Medienkarte
sind weiterhin keine Systemdateien nötig. Nur für ein Update wird ein
speziell verpacktes Image im Hauptverzeichnis der Karte abgelegt.

## Bedienung

1. Passendes Paket als `firmware-update.bin` auf die FAT32-Karte kopieren.
   Ein rohes FEL-Image nur umzubenennen genügt nicht.
2. Kamera mit angeschlossenem Display und stabiler USB-Stromversorgung starten.
3. Nach der Dateiprüfung erscheint die Updateabfrage. **OK zwei Sekunden
   halten**, um zu installieren; eine andere Taste oder 30 Sekunden ohne
   Bestätigung überspringen das Update.
4. Während Schreiben, Rückleseprüfung und Neustart die Versorgung nicht trennen.

Das Programm prüft Paketgröße, Format, Boardkennung, SHA-256, die feste
Partitionsaufteilung, NOR-Geometrie, den zum Image passenden vorhandenen
Bootloader und die vom PMIC gemeldete externe Versorgung. Eine Karte wird nur
im Startfenster geprüft; bei offener Aufnahme-/Wiedergabedatei beginnt kein Update.
Die Versorgungserkennung garantiert keine unterbrechungsfreie Stromquelle.

Geschrieben werden ausschließlich **rootfs, Kernel und Bootlogo**; unveränderte
Partitionen werden übersprungen. Bootloader, Bootumgebung, UDISK und das
Einstellungs-Overlay einschließlich WLAN-Konfiguration bleiben erhalten.
Dies ist deshalb kein vollständiger Ersatz für eine FEL-Komplettwiederherstellung.
Ein Update setzt eine funktionierende bisherige Linux-/App-Installation voraus.

Vor der Übergabe an die RAM-Umgebung wird das Paket in
`firmware-update.installing` umbenannt. Nach erfolgreicher Rückleseprüfung
heißt es `firmware-update.done`; ein Statusprotokoll heißt `firmware-update.log`.
Diese Dateien können anschließend von der Karte entfernt werden. Ein
abgebrochener Versuch wird nicht automatisch wiederholt. Bei einem Abbruch
während des Schreibens kann FEL erforderlich sein. Es gibt keine zweite
Firmwarebank und keinen automatischen Rücksprung.

SHA-256 erkennt Beschädigungen, ist aber **keine digitale Signatur**. Nur eigene,
geprüfte Pakete für dieses Board verwenden. Die mitgelieferte Modellkennung
ist keine universelle Erkennung aller unter „V316“ verkauften Kameras.

## Bauen

Der statische ARM-Updater wird mit Zig 0.14.1 gebaut:

```powershell
python tools/sd_update/build.py --zig D:/path/to/zig.exe --output ../internal-image-build/sd-update/updater
python tools/build_internal_image.py --assemble
python tools/verify_internal_image.py
python tools/sd_update/package.py ../internal-image-build/V316CM_STANDALONE_16MiB.bin ../internal-image-build/firmware-update.bin
```

Der Paketbauer prüft zusätzlich Kernel-Header-/Daten-CRC und SquashFS-Größe.
Als Quelle dient das aktuelle eigenständige Image mit eingebautem Updater,
nicht die ältere öffentliche Rettungsbasis. Das Paket enthält das private Image
einschließlich dessen WLAN-Daten und wird **nicht in Git oder ein Release geladen**.

## Technischer Ablauf und Tests

`S01app` startet die einmalige Prüfung im Hintergrund. Die Kamera-App wird
während der unabhängigen Displayabfrage pausiert. Nach Bestätigung ersetzt
eine nur im RAM eingebundene `inittab` die normale Init-Konfiguration.
BusyBox `RESTART`/SIGQUIT beendet die anderen Prozesse und führt den statischen
Updater als PID 1 aus. Er lädt das geprüfte Image in den RAM, wechselt per
`pivot_root` auf tmpfs und hängt alle Flash-Dateisysteme vollständig aus.
Erst danach darf der Schreibpfad laufen. Kein `umount -l` und keine Bibliothek
aus dem alten Root-Dateisystem werden dafür verwendet.

Der vorhandene Herstellerkernel registriert keinen MTD-Character-Treiber;
die `/dev/mtdN`-Dateien lassen sich trotz vorhandener Nodes nicht öffnen.
Der Updater verwendet deshalb den NOR-Blocktreiber `/dev/mtdblockN`, der
Löschen und Schreiben übernimmt. Nach `fsync` und Cache-Invalidierung erfolgt
ein vollständiger byteweiser Vergleich der geschriebenen Partition.
Referenzen: [BusyBox Init](https://git.busybox.net/busybox/tree/init/init.c?h=1_25_stable),
[Linux 4.9 mtdblock](https://github.com/torvalds/linux/blob/v4.9/drivers/mtd/mtdblock.c).

Prüfwerkzeuge:

- `--check PAKET`: Format und SHA-256, ohne Flash-Schreiben.
- `--preflight PAKET`: zusätzlich Hardware, Bootloader und Versorgung.
- `--namespace-test PAKET`: isolierter Mount-Namespace, RAM-Wechsel und
  Flash-Lesevergleich; kein Flash-Schreiben und kein Neustart. Die Binärdatei
  muss dazu bereits auf einem eigenen tmpfs unter `/tmp/v316-update` liegen.
- `sd_update.sh prepare-test`: echter Init-/RAM-Wechsel mit Neustart, jedoch
  ohne Flash-Schreiben. Das Paket bleibt unverändert; Protokoll
  `firmware-update-test.log` auf SD.
- `test_device.py --evidence PRIVATER_PFAD`: Ablehnung beschädigter, verkürzter,
  fremder und unbekannter Pakete sowie PID-1-Schutz; Flash-Hashes vorher/nachher.

Die Schreibphase kann nur als PID 1 nach dem Aushängen erreicht werden.
`bootstrap.sh` ist die einmalige Installationsbrücke für den bisherigen
Firmwarestand: Updater und Startskript liegen vorübergehend im Overlay.
Nach dem ersten erfolgreichen SD-Update entfernt die Brücke diese Dateien
direkt aus dem Overlay-Upperdir, damit künftig die Version aus dem neuen
Image verwendet wird. Benutzereinstellungen werden dabei nicht entfernt.

Installation dieser Brücke über die bestehende UART-Shell (startet selbst
noch keinen Flash-Vorgang):

```powershell
python tools/sd_update/deploy.py --updater ../internal-image-build/sd-update/updater --backup ../internal-image-build/sd-update/bridge-backup --install-bootstrap
```

Der Sicherungsordner muss neu sein und bleibt privat. Paket danach auf SD
kopieren und normal neu starten. Eine Kamera, die nicht mehr bootet, benötigt
weiterhin die [FEL-Wiederherstellung](RECOVERY.md).

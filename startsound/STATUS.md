# Startsound — Stand 02.11.2026

## Neuer, nachgeprüfter Stand (ersetzt die damaligen Vermutungen unten)

- Neuester Stand ersetzt den verzögerten Menü-Helfer:
  `docs/GUI_STARTUP_2026-11-02.md`. Hintergrund-Löschen respektiert jetzt den
  HDC/Zeichenbereich; automatisches Öffnen erfolgt auf dem GUI-Thread.
  Helfer und künstliche Start-Tastendrücke entfernt. RAM-Test und installierter
  Neustart geprüft; 40-Bild-Folge ohne schwarzen Rückfall nach erstem Menübild.
  Aktuelle App MD5 `c06e035bc0262bc55de95849c5110297`, Rootfs MD5
  `8e132c1f4f931fdb903c016326bb6c49`. Startsound unverändert.
  Bevorzugtes aktuelles Rettungsimage:
  `D:\ct9000\gui-startup-fix-20261102\V316CM_GUI_STARTUP_PRIVATE_16MiB.bin`.
  Abschaltton funktioniert; Abschaltbild beim letzten Test weiterhin nicht
  sichtbar und ausdrücklich noch nicht als repariert bestätigt.
- Menü-Startfehler anschließend behoben (siehe `docs/BOOT_MENU_2026-11-02.md`):
  Menü wurde automatisch geöffnet, danach aber durch späte Startzeichnungen
  übermalt. LCD blieb an, Fensterstatus blieb sichtbar, Bildpuffer war dunkel.
  Ein einmaliger Starthelfer ruft das Menü nach der Initialisierung erneut auf.
  Alte Overlay-Version von S01app reversibel nach
  `/overlay/recovery-S01app-before-boot-menu` verschoben.
  Zwei Neustartprüfungen: alle vier Kacheln im Bildpuffer sichtbar, App stabil,
  Rootfs und unveränderter lauterer Startsound per MD5 bestätigt.
  Neues bevorzugtes Rettungsimage mit bereinigtem Overlay:
  `D:\ct9000\boot-menu-fix-20261102\V316CM_BOOT_MENU_RESCUE_PRIVATE_16MiB.bin`.
- Aktuell installiert: `neu1_gain2_limited.wav` aus `neu1.wav` mit Faktor 2
  (+6,02 dB) vor einem Lookahead-Limiter (Limit 0,98, Attack 5 ms,
  Release 50 ms, kein Auto-Level). Original unverändert erhalten.
  Gemessener mittlerer Pegel +2,1395 dB; Spitzen müssen begrenzt werden,
  weil bereits das Original 0 dBFS erreicht. Länge und Format unverändert.
  Image/Paket/Prüfsummen/Geräteprüfung:
  `D:\ct9000\startup-neu1-gain2-limited-20261102\`.
  Nach Installation und Neustart geprüft: aktive WAV MD5
  `d7fd94bb2a8b9c392a37d66e6c8515e9`; Rootfs MD5
  `81a5eca850d4bde605e9a6772b88d63a`; beide identisch zur Build-Ausgabe.
  `sdvcam` PID 758 stabil, Updater meldet vollständige Rückleseprüfung.
  Voriges SD-Paket erhalten als `/mnt/extsd/firmware-update-neu1.done`.
  Software-Tastenbestätigung im Update-Dialog wirkungslos; Installation
  mit ausdrücklicher Benutzerfreigabe über den vorhandenen RAM-/PID1-
  Updater gestartet. Hörprobe durch Benutzer noch offen.
- Linux und UART waren erreichbar. `sdvcam` lief beim Welcome-Hänger nicht.
- Der aktive `startup.wav` war eine 20-Byte-Overlay-Datei mit dem Text
  `gzip: invalid magic\n`. Die intakte SquashFS-Datei darunter blieb erhalten
  (158804 Byte, MD5 `18b0542c4ff38064e9e8667dd61326b4`).
- Defekte Datei reversibel nach `/overlay/recovery-startup.wav.corrupt-20b`
  verschoben. Nach Neustart lief `sdvcam` wieder. Overlay: 71 %, 148 KiB frei.
- Neues privates Rettungsimage des reparierten Kamerastands:
  `D:\ct9000\rescue-rebuilt-20261102-verified\V316CM_RESCUE_PRIVATE_16MiB.bin`.
  SHA256 `cc0345e6bf861099fea8e706ff570ab21c3627abc8758c4ca819988b5e2f0071`.
  Alle Partitionen per Kamera-MD5 geprüft, unveränderliche Flashbereiche
  zweimal erneut verglichen, alle 671 regulären Rootfs-Dateien lokal gelesen.
  Dies ist noch keine FEL-Rückleseprüfung nach einer Wiederherstellung.
- SD-Rettungspaket, Manifest und SHA256SUMS liegen im gleichen Ordner.
- Gewünschter neuer Startsound: `startsound/neu1.wav`, unverändert PCM Mono,
  16 Bit, 44100 Hz, 6,752925 s. SHA256
  `c773447c15b6aed9f81bb45ff763f2bf838e109ac5729a0a2d2cb4812eade69d`.
- Neues Sound-Image und Paket: `D:\ct9000\startup-neu1-20261102\`.
  Nur `usr/share/minigui/res/audio/startup.wav` geändert; 1114 Tar-Einträge
  einschließlich Metadaten verglichen. Rootfs 10346496 / 11010048 Byte.
  Paket auf SD hochgeladen, Kamera-Prüfsumme und Updater-Preflight erfolgreich.
  Installation über den bestehenden SD-Updater bestätigt und erfolgreich:
  Rootfs geschrieben und vollständig zurückgelesen, Kernel/Bootlogo identisch.
  Nach Neustart: aktive WAV 595652 Byte, MD5
  `b27d58a1bff1ccdec95e00974af7224f`, identisch zu `neu1.wav`.
  Rootfs auf Flash: MD5 `03a3b59fdf9b209a6f4d175677f1afc7`, identisch
  zum neuen Image. `sdvcam` PID 758 läuft über zwei Prüfzeitpunkte stabil,
  GUI verarbeitet Tasteneingaben. Hörprobe durch den Benutzer noch offen.
  Abgeschlossenes Paket auf Kamera: `/mnt/extsd/firmware-update.done`.

Die unten genannten früheren privaten Rettungsdateien waren am 02.11.2026
nicht mehr vorhanden. Die folgende Rekonstruktion bleibt als Historie erhalten;
ein voller Overlay oder zwei App-Prozesse sind nicht als aktuelle Ursache belegt.

## Historische Notiz vor der UART-Diagnose

## Was passiert ist (Rekonstruktion)

1. Ziel: neuer Startsounds statt `startup.wav` (44,1 kHz / 16 Bit / Mono, 200.202 B, MD5 `4395bae6…`).
2. Original-WAVs per UART von der Kamera gesichert → `firmware/audio_orig/`.
3. Neuer Sound erzeugt (`firmware/startup_new.wav`, Arpeggio; später `startsound/chord_1p8.wav`, Akkord 1,8 s).
4. Upload nach `/tmp/startup_new.wav` auf der Kamera: **MD5-identisch verifiziert** (`03845dc1…`).
5. **Fehler 1:** Backup `cp startup.wav /data/startup_orig.wav` meldete Erfolg, war aber **0 Byte** — `/data` liegt im JFFS2-Overlay, das zu dem Zeitpunkt voll war.
6. `kill 759` (sdvcam) → App lief sofort wieder an (Init-Respawn).
7. **Fehler 2:** Tauschversuch gegen die read-only SquashFS schlug fehl („No space left on device" wegen vollem Overlay); parallel wurde eine **zweite sdvcam-Instanz** (PID 2086) manuell gestartet. Zwei Instancen kämpften um `/dev/snd/pcmC0D0p` und Display/WindowManager.
8. Danach: Kill von 2086 → UART-Shell tot → Power-Zyklus → **Bootloop**. Ursache mit hoher Wahrscheinlichkeit die Doppel-Instanz plus voller Overlay (config-Partition): Init stirbt in kritischer Phase oder schreibt Boot-Fehlerzustand ins JFFS2.
   *Das ist eine begründete Vermutung, kein Beweis — das Bootlog ging auf COM11 nicht mehr mit.*

## Aktuelle Flash-Stände (MD5, alle 16 MiB)

| Datei | MD5 | Bedeutung |
|---|---|---|
| `D:\ct9000\fel-setup-repair-20261101\repair-full-private.bin` | `3165f4a187086ce8c24c357e6cd16269` | **Letzter FEL-verifizierter, gerät-getesteter Stand** (verification.json: „FEL verified; SETUP + PHOTO/VIDEO/STREAM ok"). Basis für alles Weitere. |
| `D:\ct9000\fel-repair-20261101\repair-full-private.bin` | `eebe3965702ef368a927c61a42df471d` | Vorgänger-Stand vom 01.11. |
| `D:\ct9000\v316-cam-unbrick\firmware\V316CM_WORKING_FULL_IMAGE_16MB.bin` | öffentliches Referenzimage | NICMHT diese Kamera-Konfiguration (älter). |

## Fertiges SD-Rettungs-/Update-Paket (Startsound AKKORD)

- Rootfs-Basis: last-good-SquashFS aus `3165f4a1…` extrahiert, nur `usr/share/minigui/res/audio/startup.wav` ersetzt durch `chord_1p8.wav` (MD5 `18b0542c…`). Alle übrigen Bytes unverändert.
- Image: `D:\ct9000\startsound-work\V316CM_STARTSOUND_16MiB.bin` — MD5 `4ce4f53a23df59bd0b22446f6a7ed375`
- Paket:  `D:\ct9000\startsound-work\firmware-update.bin` — MD5 `70c0149cf2de28ccca2503c668384b45`, 16.777.728 B
  Header: Magic `V316-SDUPDATE1`, Board `V316-A14018-16M`, SHA256 über Payload = `ff4b…`→neu: korrekt gesetzt, bei Bau konsistenzgeprüft.
- Updater schreibt **nur rootfs/kernel/bootlogo**; Bootloader, UDISK und **JFFS2-Einstellungen bleiben erhalten**.

## Wiederherstellungsweg (in dieser Reihenfolge)

### Weg A — SD-Updater (bevorzugt, wenn die Kamera bis zum Update-Dialog bootet)
Der Updater läuft am Ende der Initialisierung und fragt 30 s lang (docs/SD_UPDATE.md):
1. SD-Karte **FAT32**, `firmware-update.bin` aus `D:\ct9000\startsound-work\` ins Hauptverzeichnis kopieren, sicher auswerfen.
2. Karte in die **ausgeschaltete** Kamera, USB-Datenkabel anschließen (Updater braucht keinen Akku, stabile USB-Versorgung).
3. Starten; erscheint die Update-Abfrage: **OK/Auslöser 2 Sekunden halten** → Installation inkl. Rückleseprüfung.
4. **Wichtig:** Wenn die Kamera gar nicht erst bis zum Dialog kommt (sofort Reset), ist Weg A tot → Weg B.

### Weg B — FEL (bringt den guaranteed-good-Stand zurück)
Nach docs/RECOVERY.md: Kamera stromlos, FEL-Kontakt auf Masse, USB-Datenkabel:
```
sunxi-fel -l
sunxi-fel spiflash-info
sunxi-fel -p spiflash-write 0 D:/ct9000/fel-setup-repair-20261101/repair-full-private.bin
sunxi-fel -p spiflash-read 0 16777216 after.bin
# MD5 beider Dateien vergleichen (after.bin == 3165f4a1…)
```
FEL-Toolchain liegt unter `D:\ct9000\sunxi-tools` bzw. `sunxi-tools1`.

**Empfehlung:** Erst Weg B (Rückkehr auf last-good), dann Bootloop-Ursache klären (Overlay-Vollstand!), dann Startsound **nur noch über SD-Update-Paket** einspielen — niemals zwei sdvcam-Instanzen, niemals cp auf volle Partition ohne Größen-/RC-Check.

## Regeln für künftige Live-Tests (Lessons Learned)
1. Vor jedem Schreiben auf die Kamera: `df` prüfen; `/data`-Schreibaktionen immer mit `ls -l`-Gegenprobe.
2. sdvcam nie doppelt starten; Respawn des Init abwarten (2× `ps` im Abstand).
3. Kein Tausch von Rootfs-Dateien zur Laufzeit — Rootfs ist read-only SquashFS; Änderungen gehören ins Build-Image + SD-Update.
4. WAV-Zielformat: 44,1 kHz, 16 Bit, Mono, PCM unkomprimiert (Player prüft strikt).

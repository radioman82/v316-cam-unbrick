# Startsound — Stand 02.11.2026 (Bootloop nach Live-Tausch, Rettung vorbereitet)

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

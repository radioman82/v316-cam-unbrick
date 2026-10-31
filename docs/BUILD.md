# Internes Image bauen

Das getestete Komplettimage enthält private WLAN-Daten und bleibt lokal.
Die öffentliche 16-MiB-Datei ist die ältere Rettungsbasis. Für einen eigenen
Build wird eine eigene gesicherte Laufzeitinstallation benötigt.

## Voraussetzungen

- Windows, Python 3, Pillow und pyserial: `python -m pip install Pillow pyserial`.
- Arm GNU Toolchain arm-none-eabi 13.3 rel1 und Segoe UI; Toolchain-Pfad
  in `tools/ui_theme/build.py`.
- Windows-/Cygwin-SquashFS-Tools mit XZ, Symlinks und Pseudo-Gerätedateien;
  getestet mit Version 4.3.
- Passende Referenzfirmware für dieses Board.

Die zwei App-Basen `sdvcam_v8` und `sdvcam_menu_v22` bleiben nötig:
`build_menu_v22.py` erzeugt v22 aus v8; der Renderer baut darauf auf.
Dies patcht geprüfte Binärbasen und ist kein vollständiger Quell-Neubau der
herstellerspezifischen Kamera-App.

## Ablauf

1. Privat sichern, siehe [RECOVERY.md](RECOVERY.md).
2. `python tools/capture_runtime.py --source internal`; für den früheren
   SD-Stand `--source sd`. Export nach `../internal-image-build/runtime/`,
   einschließlich privater WLAN-Datei. Lokale identische Dateien dienen
   als Cache; fehlende Dateien werden per UART gelesen.
3. `python tools/ui_theme/build.py --internal`.
4. `firmware/splash/welcome.bmp` und `byebye.bmp` vorbereiten:
   320 × 240 Pixel, RGB 24 Bit, unkomprimiert.
5. Image bauen:

    python tools/build_internal_image.py --assemble --squashfs-tools D:/path/to/squashfs_tools

`--work-dir` ändert den privaten Arbeitsordner; der Runtime-Export muss dann
in dessen Unterordner `runtime/` liegen. Lokale CRC-gültige
Einstellungssicherungen werden berücksichtigt. Fehlen sie, bleiben Werkswerte
mit deutscher Startsprache. Verwendete Quelle im Manifest kontrollieren.

Ausgaben: `standalone.squashfs`, `V316CM_STANDALONE_16MiB.bin` und
`manifest.json` außerhalb des Repositorys. Der Builder prüft Referenz-SHA,
Partitionsgröße und setzt UNIX-Rechte, Symlinks und Gerätedateien. Er ersetzt
SD-Systempfade und entfernt das Stock-Kopieren der App auf SD. JFFS2 wird
beim ersten Start aus einem leeren Bereich angelegt.

## Prüfen und installieren

`python tools/verify_internal_image.py` prüft den Standard-Arbeitsordner:
Extraktion, Inhalte, Symlink-Ziele, ELF-Bibliotheksnamen und interne
Startpfade. Ein kleiner XZ-Mount auf der erreichbaren Kamera prüft die
Kernel-Unterstützung im RAM, ohne den Flash zu ändern.

Danach FEL-Installation und vollständige Rücklesung, Kaltstart ohne SD,
Menüs/STREAM sowie Aufnahmeprüfung mit leerer Medienkarte. Zeitstempel
können die SHA-256 eines Neubaus ändern; sein eigenes Manifest ist maßgeblich.

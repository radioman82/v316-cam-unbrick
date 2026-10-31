# Menü-Renderer und deutsche Ressourcen

Aktuell: [interne Firmware vom 31.10.2026](../../docs/INTERNES_IMAGE_2026-10-31.md).

Der Renderer ergänzt die ARM32-App um einheitliche Listen und Dialoge,
deutsche Texte, das Startmenü und die Trennung von FOTO/VIDEO und STREAM.
Native Auswahl- und Einstellungsfunktionen bleiben erhalten; Aufnahmebefehle
sind in STREAM gesperrt. Doppelte native Kachelbeschriftungen entfallen,
weil die Kachelbilder bereits Text enthalten. Der Wrapper erhält insbesondere
das vom vorhandenen Modusfilter benötigte Register `r4`.

Der Builder prüft die v22-Basis und die alten Bytes jeder Hookstelle. Ein
zusätzliches RX-ELF-Segment enthält Renderer und Glyphenatlas.

    python tools/ui_theme/build.py --internal

Die interne Ausgabe unter `firmware/ui_internal/` wird generiert/ignoriert.
Ohne `--internal` entsteht die bisherige SD-Variante unter `firmware/ui_theme/`.
Beide enthalten „Flimmerreduzierung“ und sichtbare Fototexte mit „Foto“;
interne Kennungen wie `ml_photo_resolution` bleiben unverändert.

Voraussetzungen: Python/Pillow, Segoe UI und Arm GNU Toolchain arm-none-eabi
13.3 rel1. Gesamtes Image: [BUILD.md](../../docs/BUILD.md).

`deploy.py` und `deploy_startup.py` sind **Legacy-SD-Installer**, nicht der
Installationsweg für das interne Image. Die lokale Root-Wartungsschnittstelle
`/tmp/v316cm-ui-command` wird atomar per temporärer Datei und Umbenennen
beschickt; die Streaming-Website benutzt sie nicht.

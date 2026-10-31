# Geprüfter Kamerastand vom 31.10.2026

Die Kamera verwendet ein eigenständiges internes Image. Installation,
Kaltstart ohne SD, Streaming und Aufnahme auf leerer Medienkarte sind geprüft.

## Aufbau

| Bestandteil | Speicherort |
| --- | --- |
| Kamera-App | `/usr/bin/sdvcam` |
| Bilder, Layouts, deutsche Texte | `/usr/share/minigui/res/` |
| Streaming, Website, WLAN-Programme/Bibliotheken | `/opt/cam/` |
| Dauerhafte Einstellungen und WLAN-Konfiguration | `/data/`, internes Overlay |
| Laufzeitdateien und Protokolle | RAM unter `/tmp` |
| Fotos, Videos und Medien-Begleitdateien | `/mnt/extsd/DCIM/` |

Unveränderte Partitionsgrenzen. XZ-SquashFS: 9.924.608 von 11.010.048 Byte,
Reserve 1.085.440 Byte; 128-KiB-Block-/Wörterbuchgröße. Kernel-Unterstützung
wurde praktisch durch einen separaten XZ-Mount geprüft. JFFS2 wurde sauber
neu angelegt; gültige Kameraeinstellungen wurden aus der Sicherung gerettet.

## Installation und Ergebnis

Zuvor meldete das laufende Linux SquashFS-/JFFS2-Fehler und wechselnde
Prüfsummen unveränderter Flashbereiche. Zwei vollständige FEL-Lesungen waren
dagegen identisch; Bootloader und RootFS entsprachen der funktionierenden
Referenz. Die Ursache des Linux-Leseverhaltens ist nicht abschließend geklärt.

Das neue Image wurde über FEL geschrieben und vollständig zurückgelesen.
Image und Rücklesung haben dieselbe SHA-256:

    7825c81f38e641e9d48c2d11c5a6fc6e1fe5652e98278fa00157a7d725d59820

Dies ist die Kennung des **privaten gerätespezifischen** Images, nicht der
älteren öffentlichen Rettungsbasis.

Das Abschaltbild wurde anschließend durch die korrigierte Version mit
„Bye Bye“-Schriftzug ersetzt. Die aktive Datei wurde auf der Kamera per MD5
`09b50077c5cef909c0c982f91958b155` bestätigt und liegt dauerhaft im internen
Overlay. Die README-Vorschau und die Build-Eingabe sind ebenfalls aktualisiert.
Das private Komplettimage wurde damit neu gebaut und auf Dateiintegrität
geprüft (SHA-256 `2c6bee406178b24a542211772e9713bd650369dfce2ceed822229a88d2f8c942`);
dieser Neubau wurde nicht erneut komplett geflasht. Der vorherige, auf dem
Gerät geprüfte Image-Stand bleibt lokal gesichert. Eine Sichtprüfung des
Bildes während des tatsächlichen Ausschaltens steht noch aus.

- Kaltstart ohne SD, keine SD-Geräte oder SD-Bind-Mounts.
- Geräte-Setup zeigt Deutsch und „Flimmerreduzierung“ korrekt.
- WLAN, HTTP und zehn unterschiedliche, vollständig dekodierte
  320 × 240-Kamerabilder ohne SD; Nutzer bestätigt Livebild.
- Ohne angeschlossenes Display: schwarze JPEGs, keine Display-Interrupts.
  Mit Display und demselben Image: funktionierendes Livebild nach Kaltstart.
- Leere 32-GB-Karte erkannt; keine Systemdateien darauf erzeugt.
- Foto vollständig dekodiert: 3264 × 2448 Pixel.
- Video: 7,034 Sekunden, H.264 1920 × 1080 und AAC-Tonspur;
  alle 831 Videoframes dekodiert. `.sec` und `.thm` sind native
  Medien-/Vorschau-Begleitdateien.
- Nach Aufnahme wieder fünf unterschiedliche Streaming-Bilder.
- Aufnahmeprüfung ohne Akku über externe Versorgung.
- Keine SquashFS-Dekompressions-/JFFS2-Daten-CRC-Fehler in den geprüften
  neuen Start-/Aufnahmeprotokollen.

Native Album-Bedienung, akustische Tonqualität und alle weiteren
Aufnahme-Untermodi sind nicht separat geprüft. Der Versorgungstest ist
keine Zusage für beliebige Netzteile oder Spannungsausfälle.

Sicherungen und privates Image bleiben außerhalb von GitHub.
[Build-Anleitung](BUILD.md) · [Recovery](RECOVERY.md).

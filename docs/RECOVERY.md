# Sicherung und Wiederherstellung

Für das geprüfte Board mit 16-MiB-Fudan-Flash (`a1 40 18`).
Anschlussbelege: `hardware/`. UART: COM11, 115200 Baud, 8N1, kein Flow Control.
Passende Logikpegel, gemeinsame Masse, TX/RX gekreuzt; keine
Adapter-Versorgung auf RX/TX legen.

## Anschlussfotos dieses Boards

Das beschriftete Foto zeigt die nachgerüsteten Leitungen für GND, RX, TX
und FEL. Für UART gilt: Kamera-TX an Adapter-RX und Kamera-RX an Adapter-TX.
Die Fotos dokumentieren dieses konkrete Board, keine universelle Pinbelegung.

![Beschriftete UART- und FEL-Anschlüsse](../pictures/zus%C3%A4tzliche-anschl%C3%BCsse.jpg)

[FEL-Nahaufnahme](../pictures/FEL.jpg) ·
[Antennenanschluss](../pictures/Antennenanschluss.jpg).

## Sicherung

Eigene Einstellungen und WLAN-Daten privat sichern. `backup_internal.py`
erstellt einen UART-Snapshot per geprüften Blockdifferenzen zur Referenz.
Bei wechselnden Lesungen ist dieser kein als gut bestätigter Firmwarestand.
Ein Fehler beim separaten Lesen der Einstellungen kann trotz bereits
gesicherter Flashdateien auftreten.

Bewährter Rettungsweg: **FEL über den USB-Datenanschluss**; der UART-Adapter
ist nicht diese Verbindung. Kamera stromlos machen, den am Board bereits
identifizierten FEL-Kontakt für den FEL-Eintritt mit Masse verbinden und
das USB-Datenkabel anschließen.

    sunxi-fel -l
    sunxi-fel spiflash-info
    sunxi-fel -p spiflash-read 0 16777216 before-read1.bin
    sunxi-fel -p spiflash-read 0 16777216 before-read2.bin
    Get-FileHash before-read1.bin,before-read2.bin -Algorithm SHA256

Erwartet: Allwinner V536, Flash 16.777.216 Byte, A1h/40h. Beide vollständigen
Lesungen müssen identisch sein. Neue Sicherungsdateien verwenden, alte
nicht überschreiben. Bei instabilen FEL-Lesungen zuerst die Ursache klären.

## Schreiben und kontrollieren

Nur das passende, geprüfte Image verwenden. Die öffentliche
`V316CM_WORKING_FULL_IMAGE_16MB.bin` ist die ältere Rettungsbasis, nicht
das neue SD-unabhängige Komplettimage.

    sunxi-fel -p spiflash-write 0 IMAGE.bin
    sunxi-fel -p spiflash-read 0 16777216 after-read.bin
    Get-FileHash IMAGE.bin,after-read.bin -Algorithm SHA256

Versorgung und USB während Schreiben/Prüfen nicht trennen. Erst bei
identischen Prüfsummen FEL-Kontakt lösen und normal starten. Eine Image-
Datei auf SD installiert sich nicht automatisch.

Zuerst ohne SD starten und Menüs/Streaming prüfen, dann mit leerer
Medienkarte Aufnahme testen. Display für den getesteten Stream anschließen.

Am 31.10.2026 waren die beiden vollständigen FEL-Sicherungen identisch:
`77cac7e133649db41c9d772035a5ddce90f722062805bbdd9ef2ebfeacc55cf5`.
Unter Linux beobachtete wechselnde Prüfsummen waren über FEL nicht
reproduzierbar; ein Hardwaredefekt ist damit nicht abschließend diagnostiziert.
Ein elektrisches Zeichenecho allein belegt keine funktionierende Linux-Shell.

Private Images, Rohsicherungen, WLAN-Dateien und Testaufnahmen bleiben
außerhalb von GitHub. Frühere Diagnosen sind über die Git-Historie verfügbar.

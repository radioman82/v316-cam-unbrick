# Start ohne verzögerten Menü-Workaround

Dieser Stand ersetzt `BOOT_MENU_2026-11-02.md`. Der damalige Starthelfer
zeigte das Menü nach drei Sekunden erneut an, verdeckte aber nur den Fehler.
Der Benutzer beobachtete Welcome, Vorschau, Kacheln, Schwarz und erneut Kacheln.

In `theme_window_proc` wurde `MSG_ERASEBKGND` mit einem neu angeforderten DC
und einer ungeclippten Vollflächenfüllung behandelt. Dadurch konnten bereits
gezeichnete Bedienelemente wieder übermalt werden. Die neue Implementierung
verwendet den übergebenen HDC und begrenzt die Füllung auf das übergebene,
in Client-Koordinaten umgerechnete Rechteck. Grundlage für diese Parameter:
[MiniGUI-Programmierhandbuch, MSG_ERASEBKGND](https://github.com/VincentWei/minigui-docs/blob/master/programming-guide/MiniGUIProgGuidePart1Chapter02.md).

Der Ressourcen-Callback öffnet außerdem keine Fenster mehr direkt. Er setzt
nach dem zweiten Ressourcen-Ladevorgang eine Ready-Markierung. Erst nach
einer abgeschlossenen GUI-Dispatch-Verarbeitung wird das Kachel-Menü einmal
geöffnet. Der Done-Marker wird vor dem Aufruf gesetzt, um Rekursion zu vermeiden.

Die Kombination wurde zunächst über RAM-Bind-Mounts mit genau einer laufenden
App geprüft. Keine Korrektur durch künstliche Tastenereignisse und kein alter
Starthelfer: Kacheln korrekt sichtbar, Prozess stabil. Die erste Variante nur
mit GUI-Thread-Verschiebung genügte nicht; erst die korrigierte Hintergrund-
Behandlung beseitigte die schwarze Fläche.

Installierter Stand: App MD5 `c06e035bc0262bc55de95849c5110297`, Rootfs MD5
`8e132c1f4f931fdb903c016326bb6c49`. Die Firmware wurde per SD-Updater aus dem
RAM installiert und vollständig zurückgelesen. Danach wurden App, Rootfs,
Abschluss-Paket, unveränderter lauterer Startsound und sichtbare Kacheln geprüft.
Der Helfer `/opt/cam/startup_menu.sh` und dessen Init-Aufruf sind entfernt.

Eine beim Neustart ab erster UART-Shell aufgezeichnete Folge von 40 Bildern
(etwa 0,2 s Abstand) zeigte ab Bild 8 nur noch das korrekte Kachel-Menü, ohne
schwarzen Rückfall. Null GUI-Tastendrücke im geprüften Boot-Log. Der Benutzer
bestätigte zunächst Welcome → dauerhaft Kacheln und präzisierte später eine
kurz sichtbare native Vorschau vor den dauerhaft sichtbaren Kacheln. Diese
kurze Initialisierungsansicht wurde nicht zusätzlich verdeckt.

Private Image-/Prüfdateien: `D:\ct9000\gui-startup-fix-20261102\`.
`V316CM_GUI_STARTUP_PRIVATE_16MiB.bin` ist das bevorzugte neue Komplettimage
mit bereinigtem Overlay und korrigiertem Rootfs. SHA256:
`824e4f20192bc082e480a1e20f1d245bfebe338b108030582ac780fa2d5b0124`.
Keine FEL-Wiederherstellung dieses Images durchgeführt. Enthält private Daten.

## Abschaltbild bleibt getrennt zu untersuchen

Abschaltton und Abschalt-BMP sind intakt. Beim Test vor dieser Korrektur war
das Bild laut Benutzer teilweise von Schwarz überdeckt. Beim erneuten echten
Ausschalt-Test nach dieser Korrektur meldete der Benutzer kein sichtbares Bild.
Das Abschaltbild ist damit ausdrücklich nicht als behoben bestätigt.
SD-Aufnahmen: `/mnt/extsd/shutdown-check-20261102-2`.
Das Abschaltfenster ist anhand der Factory und des Konstruktors als VTable
`0x204b8c` identifiziert; es wird bisher ebenfalls als Theme-Menü behandelt.
Eine separate Ausnahme bzw. Änderung dafür wurde noch nicht installiert.

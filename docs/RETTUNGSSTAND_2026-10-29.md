# Allwinner V316 Cam: Rettungsstand vom 29.10.2026

## Laufender Stand

- Die Kamera bootet nach der Flash-Reparatur wieder mit eingesetzter SD-Karte.
- Die App mit MD5 `4614a61766519e17a778c914956c8ff9` öffnet das
  Vier-Kachelmenü beim Start ohne Tastendruck. Vorher ist kurz das Livebild zu
  sehen. Der Kaltstart wurde am Gerät geprüft; der Menü-Framebuffer ist statisch
  (`882fff0d930173964f5fab73ca2627ce`).
- Die SD-Skripte für STREAM verwenden denselben `v316cm`-Modus-Marker wie die
  App. Nach dem Abgleich waren WLAN, HTTP und fünf unterschiedliche
  320×240-MJPEG-Bilder wieder erreichbar.
- Zwei Versuche, das kurze Livebild vollständig zu unterdrücken, führten zu
  leerem Display. Beide wurden zurückgenommen; der oben genannte Stand läuft.

## Lokale Rettungsdateien

Die vollständigen Sicherungen liegen unter `D:\ct9000\recovery-2026-10-29`.

| Datei | Zweck | SHA-256 |
| --- | --- | --- |
| `V316CM_CURRENT_WORKING_20261029_16MB.bin` | Aus funktionierendem SPI-Flash gelesenes 16-MB-FEL-Abbild | `9d464465adbcfbb33726f8bd19a532ff77b3650b9eb799a5311a00ab24c3f2d3` |
| `sd-runtime-current-20261029.tar.gz` | Passende SD-Laufzeitdateien einschließlich App und Streaming-Skripten | `47210734e015593fc94e6c2e0f51f8d40a7bd1920bf81cb53d1a582bb77b71b1` |

Das SPI-Abbild enthält den Boot-Hook, die aktuelle App und die Menüressourcen
liegen auf der SD-Karte. Beide Teile gehören für den aktuellen Funktionsstand
zusammen. Das Abbild wurde aus der laufenden Kamera gelesen und strukturell
geprüft, aber nicht testweise zurückgeflasht. Die FEL-Anleitung liegt lokal als
`FEL-WIEDERHERSTELLUNG.txt` und auf der SD-Karte. Ein auf die SD-Karte
kopiertes SPI-Abbild flasht die Kamera nicht automatisch.

Das SD-Archiv enthält private WLAN-Daten. Beide Rettungsdateien sind
gerätespezifisch und bleiben lokal; das öffentliche GitHub-Repository enthält
Quellcode, reproduzierbare App und diese Prüfsummen.

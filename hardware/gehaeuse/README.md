# CT9000 Gehäuse V12

[FreeCAD-Modell](CT9000_Gehaeuse_V12.FCStd) · [STL-Satz V12](STL_V12) · [Schiebedeckel von unten](CT9000_V11_Akkudeckel.png)

[Einbauansicht V10 mit transparentem Gehäuse](CT9000_V10_Einbauansicht.FCStd) · [Vorne](CT9000_V10_Einbau_vorne.png) · [Hinten](CT9000_V10_Einbau_hinten.png)

Die separate Einbauansicht zeigt Hauptplatine, Akku, Objektiv, Tasterplatine und LCD an ihren Positionen. Der LCD-Dummy ist ein 59 × 41 × 4,2 mm großer Referenzkörper für das Display samt Kunststoffbett. Seine Anzeige ist im Baum unter **Referenzkörper** schaltbar.

Das Modell ist ein Konstruktionsstand für den Maßabgleich. In FreeCAD stehen die Eingabemaße und berechneten Maße im Objekt **Maße (mm)**. Gelistete Entwurfswerte lassen sich dort ändern. Die acht Bauteile bestehen aus nativen FreeCAD-Volumenkörpern.

| Bauteil | Auslegung |
| --- | --- |
| Vorderwanne | 63,6 × 45,6 × 34,4 mm Gehäuse insgesamt, 2 mm Wandstärke. Breite und Höhe ergeben sich aus dem LCD-Bett mit 0,3 mm Luft je Seite und den Wänden. |
| Objektiv | Achse 13 mm von der rechten und oberen Platinenkante. Ø 19 mm Durchlass, Ø 16,8 mm gemessene Linse. Linsenrand 28 mm vor Platinenfläche, davon im Modell 3 mm vor dem Gehäuse. Hinterer Tubus aus dem seitlichen Akkuspalt vereinfacht modelliert. |
| Rückrahmen | Tasche 59,6 × 41,6 mm für das bestehende 59 × 41 × 4,2 mm große LCD samt Bett. Umlaufende 1 × 1 mm Auflage. Das 57 × 39 mm große Fenster ist mit der sichtbaren Fläche abzugleichen. |
| Akku | Fach links vom Objektiv mit 2-mm-Führungen. Die Führung zur Linse ist im Objektivbereich ausgespart. Die gemessene Akkulage nutzt die vorhandenen Kontaktpfosten auf der Platine. Einschub von unten, 29,8 mm quer und 33 mm in Einschubrichtung. Ausschnitt 30,6 × 11,8 mm, bündiger Schiebedeckel mit vier Haken. |
| Hauptplatine | Drei Auflagen auf der Linsenseite der Platine. Die Platine lässt sich von hinten einsetzen und verschrauben. Außendurchmesser 4,5 mm und Pilotbohrungen 1,6 mm. Die linken Auflagen sind 3 mm hoch, die rechte 1,5 mm mit 0,5 mm Abstand zur Akkurückseite. Die Schraubenlänge rechts muss zum flachen Dom passen. |
| Druckkappen | Oben und vorn rund, links zwei längliche Kappen. 2,5 mm Überstand, 0,25 mm Luft je Seite, innen Halteflansch und Druckstift. Druckstiftlängen und Hub sind vorläufig. Die Mitte der Fronttaste ist für den geraden Einbau gegenüber V5 um 6,7 mm zur Gehäusemitte versetzt. |
| Mini-USB und Mini-HDMI | In der rechten Seitenansicht mit Linse oben sitzt Mini-USB rechts und Mini-HDMI links davon. Mini-USB 8,5 × 3,5 mm, Mini-HDMI 8,5 × 3 mm. Die Unterkanten liegen bündig, der seitliche Steg ist 2 mm breit. |
| microSD | Schlitz 12 × 2 mm unten rechts, mit 1,5 mm Steg zur bündigen Unterkante der Buchsen. |
| Service | 4 mm weiter rechts als in V9. Die 6,8 × 3 mm große Öffnung reicht in Y von 4,1 bis 7,1 mm und liegt vollständig oberhalb der angrenzenden Bodenwand. |
| Lautsprecher | Sieben Durchgangslöcher Ø 1,6 mm links unter den Seitentastern, mit 2,7 mm Lochkreisradius. Die Mitte der Lochgruppe liegt vorläufig 8,5 mm über dem Boden und 16,3 mm vor der Rückseite. Der Durchgang ist im CAD geprüft. |

Die rechte Kante des alten, 40,5 mm langen Seitenteils entspricht in dieser Ansicht der alten Gehäuseoberseite. Der alte Umriss ist in Y mittig auf den neuen Umriss bezogen. Von der alten rechten Kante bis zur rechten Kante des microSD-Schlitzes sind es 8 mm, bis zur rechten Mini-USB-Kante 9,5 mm. In Z sind die bündigen Buchsenunterkanten vorläufig auf Höhe der Platinenfront angesetzt.

## Akkudeckel

Den Deckel nach dem Einlegen des Akkus von unten in die vier erweiterten Einsetzöffnungen ansetzen und 4 mm in Richtung der linken Gehäuseseite schieben. Die Haken greifen dann hinter den verstärkten Rand. Zum Öffnen den Deckel an der Schieberippe 4 mm nach rechts schieben und nach unten abnehmen. Die Richtungen beziehen sich auf die Vorderansicht mit der Linse rechts.

Plattenmaß 34,6 × 15,8 × 1,6 mm, nominell 0,25 mm Führungsspiel je Seite. Spiel und Hakenfestigkeit sind Entwurfswerte für einen Passversuch. In FreeCAD wurden mehrere Positionen beim Einsetzen und Schieben geprüft. Bei geschlossenem Deckel verhindert der Hintergriff das direkte Abheben. Eine Rastung gegen seitliches Aufschieben und die endgültige Fixierung des Akkus in Einschubrichtung sind offen.

## Montage der Fronttaste

1. Die runde Druckkappe von innen nach außen durch die Frontöffnung stecken. Der breitere Flansch bleibt im Gehäuse.
2. Die 13 × 13 mm große Tasterplatine mit dem Druckkopf zum Druckstift in die Tasche legen. Die Position der Tasche setzt eine mittige Taste auf der kleinen Platine voraus.
3. Die Halteplatte von hinten über die Platine setzen. Die Kabel durch das mittlere Fenster führen. Die Halteplatte an den zwei Pilotbohrungen verschrauben, anschließend Hauptplatine und Akku einsetzen.

Der Entwurf nimmt 1,2 mm Platinenstärke, 2,2 mm Höhe des ungedrückten Tasters ab Platinenfläche und 0,2 mm Ruheabstand zwischen Druckkopf und Stift an. Beim realen Taster Dicke, Kopfhöhe und Versatz des Druckkopfs von der Platinenmitte messen. Auf der Rückseite der Tasterplatine brauchen Lötstellen und Kabel Platz im Fenster der Halteplatte.

## Messbezug

Vorderansicht wie beim zusammengebauten Gerät mit der Linse rechts. X läuft nach rechts, Y nach oben, Z zur Linse. Für X und Y an der Platine ist die linke untere Ecke der Nullpunkt. Für Z an der Platine ist die linsenseitige Platinenfläche der Nullpunkt. Die FreeCAD-Baugruppe selbst beginnt links unten am Rückrahmen.

| Befestigungspunkt | X ab Platine links | Y ab Platine unten |
| --- | ---: | ---: |
| Links oben | 1,5 mm | 34,5 mm |
| Links unten | 1,5 mm | 4,8 mm |
| Rechts unten | 34,0 mm | 10,5 mm |

Der Referenzkörper zeigt die Ø-2-mm-Bohrungen. Die Außenkontur der beiden linken Aussparungen und die Bauteile auf der Platine sind vereinfacht. Die beiden linken Auflagen sind mit der linken Seitenwand verbunden, die rechte mit dem Boden.

Die linke Akkukante liegt bei X = 4 mm, die Unterkante bei Y = 2 mm und die Akkurückseite bei Z = 2 mm relativ zur Platine. Die rechte Akkukante liegt bei X = 33,8 mm, die Objektivachse bei X = 41 mm. Der seitliche Spalt zum hinteren Tubus ist auf ungefähr 1 mm geschätzt. Für den CAD-Ersatzkörper ergibt sich damit ein hinterer Durchmesser von 12,4 mm. Die Stufe zum vorderen Durchmesser liegt im Ersatzkörper 0,4 mm vor der Akkuvorderseite. Durchmesser und Stufenlage sind Modellannahmen. Die Aussparung an der Akkuführung ist für einen Freiraum von Ø 19 mm ausgelegt.

Die linke Kante des 8,6 mm breiten Kontaktblocks liegt 15 mm vom linken Platinenrand, seine rechte Kante bei X = 23,6 mm. Seine Unterkante liegt 8,5 mm unter dem oberen Platinenrand, also bei Y = 29 mm. Der maximale Überstand inklusive Kontakte beträgt 6 mm ab Platinenfront. Die Bezugslinie unter **Referenzkörper** zeigt die gemessene Breite. Für einen Hüllkörper fehlt die obere Begrenzung. Die Zuglaschenbreite ist mit etwa 3 mm eingetragen.

## Druckbare Prüfteile

- [Platinen-Dummy](Pruefteile/CT9000_Platinen_Dummy.stl) mit 54 × 37,5 × 1 mm und drei Ø-2-mm-Bohrungen. Die vereinfachte rechteckige Platine dient zur Prüfung der Auflagen und Lochmitten. Bauteile, Kontaktblock und seitliche Aussparungen sind in diesem Prüfkörper ausgelassen.
- [Akku-Dummy](Pruefteile/CT9000_Akku_Dummy.stl) mit 29,8 × 33 × 11 mm für den Einschub und die Führungen. Eine Schlaufe aus dünnem Klebeband kann beim Herausziehen als Zuglasche dienen.

Beide STL-Dateien in Cura in Millimetern bei 100 % Skalierung importieren. Sie liegen bereits flach auf Z = 0. Vor dem Einpassen die gedruckte Dicke und bei der Platine die drei Lochdurchmesser prüfen.

## Maße für die mechanische Freigabe

1. **Schnittstellen.** Die provisorischen Öffnungen in Y/Z mit der bestückten Platine abgleichen. Bei USB und Mini-HDMI auch die Abmessungen der Steckergehäuse berücksichtigen. Bei microSD die Position der Kartenkante in eingesetztem und ausgeworfenem Zustand prüfen.
2. **Taster.** Bei den linken Tastern die beiden Mittelpunkte vom unteren Platinenrand und ihre Tiefe zur Platinenfläche messen. Bei 5 mm Tasterlänge und je 9 bzw. 10 mm zum Platinenrand ergibt sich 8,5 mm freier Zwischenraum. Das genannte Maß ist 7,5 mm. Für die obere OK-Taste fehlt die Z-Lage des Druckkopfs. Das 5-mm-Maß ist im Modell vorläufig als Z-Abstand interpretiert. Die Position der 13 × 13 mm großen Fronttaster-Platine und die Stiftlängen werden beim Einpassen festgelegt.
3. **Akku, Objektiv und LCD.** Die Oberkante des Kontaktblocks und den Überstand der Zuglasche erfassen. Am LCD die aktive Fensterfläche und den Austritt des Flachbands messen. Daraus folgen Flexaussparung und Befestigung des Rückrahmens. Am Objektiv den Außendurchmesser an der Gehäusedurchtrittsstelle mit Ø 19 mm vergleichen.

Die Prüfung in FreeCAD deckt die acht modellierten Teile ab. Geprüft wurden der Akku-Einschub von unten sowie die geraden Einbauwege von Hauptplatine, Frontkappe, Tasterplatine und Halteplatte von hinten. Für einen vollständigen Probedruck fehlen die Befestigung des Rückrahmens, die Akkufixierung, die Flexführung und der Maßabgleich mit den realen Anschlüssen und Tastern.

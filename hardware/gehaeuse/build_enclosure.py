"""Build the editable CT9000 fit model with the Python bundled with FreeCAD."""
from math import cos, pi, sin
from pathlib import Path

import FreeCAD as App
import MeshPart
import Part  # Registers the native Part feature types.


HERE = Path(__file__).resolve().parent
doc = App.newDocument("CT9000")
doc.Label = "CT9000 Gehäuse V12"
sheet = doc.addObject("Spreadsheet::Sheet", "Dimensions")
sheet.Label = "Maße (mm)"
sheet.set("A1", "Maß")
sheet.set("B1", "Wert")
sheet.set("C1", "Status / Bezug")
sheet.setColumnWidth("A", 235)
sheet.setColumnWidth("B", 115)
sheet.setColumnWidth("C", 400)

dimensions = [
    ("Wall", "Gehäusewand", 2, "PLA+"),
    ("BoardW", "Platine Breite", 54, "Hauptplatine"),
    ("BoardH", "Platine Höhe", 37.5, "Hauptplatine"),
    ("BoardT", "Platine Dicke", 1, "Hauptplatine"),
    ("LCDW", "LCD Breite", 59, "Mit vorhandenem Kunststoffbett"),
    ("LCDH", "LCD Höhe", 41, "Mit vorhandenem Kunststoffbett"),
    ("LCDT", "LCD Dicke", 4.2, "Mit vorhandenem Kunststoffbett"),
    ("LCDPlay", "LCD Luft je Seite", 0.3, "Entwurfswert"),
    ("LCDLip", "LCD-Auflage und Überstand", 1, "Umlaufende Auflage; Sichtfenster prüfen"),
    ("LCDGap", "LCD axiale Luft", 0.2, "Entwurfswert"),
    ("BoardRearGap", "Abstand Platine hintere Trennfuge", 3, "Entwurfswert für SD-Slot und Flex"),
    ("LensRight", "Linsenmitte von Platine rechts", 13, "Blick auf die Vorderseite"),
    ("LensTop", "Linsenmitte von Platine oben", 13, "Blick auf die Vorderseite"),
    ("LensLength", "Linsenrand vor Platine", 28, "Senkrecht zur Platine"),
    ("LensDiameter", "Linsendurchmesser", 16.8, "Gemessene Linse"),
    ("LensHole", "Öffnung für Linse", 19, "Vorgabe; Außendurchmesser Tubus prüfen"),
    ("LensOut", "Linsenüberstand vor Front", 3, "Entwurfswert"),
    ("LensBatteryGap", "Seitlicher Spalt Akku zum Tubus", 1, "Geschätzt am realen Aufbau"),
    ("BatteryW", "Akku quer zur Einschubrichtung", 29.8, "Ausrichtung nach Foto mit eingelegtem Akku"),
    ("BatteryH", "Akku in Einschubrichtung", 33, "Ausrichtung nach Foto mit eingelegtem Akku"),
    ("BatteryT", "Akku Dicke", 11, "Aus Maßangabe übernommen"),
    ("BatteryPlay", "Akku Luft je Seite", 0.4, "Entwurfswert"),
    ("BatteryLeft", "Akku linke Kante ab Platine links", 4, "Vollständig eingeschobener Akku"),
    ("BatteryBottom", "Akku Unterkante ab Platine unten", 2, "Vollständig eingeschobener Akku"),
    ("BatteryZ", "Akku Rückseite vor Platine", 2, "Ab Platinenfront"),
    ("DoorTravel", "Akkudeckel Schiebeweg", 4, "Zum Öffnen nach rechts in X"),
    ("DoorPlay", "Akkudeckel Spiel je Seite", 0.25, "Entwurfswert für Passprobe"),
    ("DoorThickness", "Akkudeckel Plattenstärke", 1.6, "Bündig im Gehäuseboden"),
    ("DoorOverlap", "Akkudeckel Auflage über Akkuausschnitt", 2, "Alle vier Kanten"),
    ("DoorRimHeight", "Akkudeckel Führung Oberkante Y", 3.8, "Lokale Verstärkung im Boden"),
    ("DoorHookReach", "Akkudeckel Hakenüberstand", 1.4, "In Schließrichtung"),
    ("PullTabWidth", "Zuglasche Breite", 3, "Ungefähr; Überstand und genaue Lage offen"),
    ("ContactLeft", "Kontaktblock linke Kante ab links", 15, "Ab linker Platinenkante"),
    ("ContactWidth", "Kontaktblock Gesamtbreite", 8.6, "Über alle drei Kontakte"),
    ("ContactBottom", "Kontaktblock Unterkante ab oben", 8.5, "Ab oberer Platinenkante"),
    ("ContactReach", "Kontaktblock maximaler Überstand", 6, "Senkrecht ab Platinenfront, inkl. Kontakte"),
    ("TopOffsetX", "OK oben ab Platine links", 9, "Mitte"),
    ("TopOffsetZ", "OK oben vor Platine", 5, "Vorläufige Zuordnung des 5-mm-Maßes"),
    ("FrontOffsetX", "Fronttaste ab Platine links", 14.2, "Versetzt für geraden Einbau an den Platinenauflagen vorbei"),
    ("FrontOffsetY", "Fronttaste ab Platine unten", 6.5, "Vorläufig, Tasterplatine 13 × 13"),
    ("FrontBoardSize", "Fronttasterplatine Kantenlänge", 13, "Quadratisch"),
    ("FrontBoardT", "Fronttasterplatine Dicke", 1.2, "Vorläufig"),
    ("FrontSwitchH", "Fronttaster Höhe ab Platine", 2.2, "Vorläufig, bis Druckkopf in Ruhestellung"),
    ("FrontRestGap", "Fronttaste Spiel zum Druckkopf", 0.2, "Vorläufig"),
    ("FrontTravel", "Fronttaste verfügbarer Hub", 0.8, "Vorläufig, bis Halteflansch anliegt"),
    ("SideTopGap", "Seitentaste oben: Randabstand", 9, "Vorläufig als Kante-zu-Kante interpretiert"),
    ("SideBottomGap", "Seitentaste unten: Randabstand", 10, "Vorläufig als Kante-zu-Kante interpretiert"),
    ("SideSwitchLength", "Seitentaster Länge", 5, "In Y-Richtung"),
    ("SideOffsetZ", "Seitentaster vor Platine", 0.5, "Vorläufig, Mitte der Druckachse"),
    ("SpeakerY", "Lautsprecheröffnung Mitte von unten", 8.5, "Vorläufig, unter den linken Tasten"),
    ("SpeakerZ", "Lautsprecheröffnung Mitte von hinten", 16.3, "Vorläufig, vor der unteren Platinenauflage"),
    ("SpeakerHole", "Schallöffnung Durchmesser", 1.6, "Sieben Durchbrüche für Ø-10-mm-Lautsprecher"),
    ("SpeakerPitch", "Schallöffnung Radius des Lochkreises", 2.7, "Sechs Bohrungen um eine mittlere Bohrung"),
    ("ButtonOut", "Tastenüberstand", 2.5, "Alle vier Druckkappen"),
    ("ButtonPlay", "Tastenführung Luft je Seite", 0.25, "Vor dem Seriendruck am Teststück prüfen"),
    ("ButtonTravel", "Luft vor Halteflansch", 0.3, "Freigang; am realen Taster abstimmen"),
    ("ButtonStem", "Druckstift hinter Flansch", 1.5, "Vorläufig; separat pro Taste abstimmen"),
    ("ServiceY", "Serviceöffnung Mitte in Y", 5.6, "Gegenüber V9 um 4 mm nach rechts verschoben"),
    ("ServiceZ", "Serviceöffnung Mitte von hinten", 15, "Vorläufig"),
    ("ServiceW", "Serviceöffnung Breite in Z", 6.8, "Rechte Seite, quer wie auf dem Foto"),
    ("ServiceH", "Serviceöffnung Höhe in Y", 3, "Rechte Seite"),
    ("OldCaseHeight", "Altes Gehäuse: Seitenlänge in Y", 40.5, "Alte Außenkante für Seitenansicht"),
    ("OldUsbRightGap", "Mini-USB Außenkante ab alter Gehäuseoberseite", 9.5, "Nach links ab rechter Kante in der Seitenansicht"),
    ("OldSdRightGap", "microSD rechte Kante ab alter rechter Außenkante", 8, "Seitenansicht mit Linse oben"),
    ("HdmiLength", "Mini-HDMI Öffnung Länge in Y", 8.5, "Vorgabe"),
    ("HdmiWidth", "Mini-HDMI Öffnung Breite in Z", 3, "Vorgabe"),
    ("UsbLength", "Mini-USB Öffnung Länge in Y", 8.5, "Korrigiertes Maß"),
    ("UsbWidth", "Mini-USB Öffnung Breite in Z", 3.5, "Vorgabe"),
    ("PortWeb", "Steg zwischen Mini-HDMI und Mini-USB", 2, "Kante zu Kante"),
    ("SdW", "microSD Öffnung Länge in Y", 12, "Vorgabe"),
    ("SdH", "microSD Öffnung Höhe in Z", 2, "Vorgabe"),
    ("SdWeb", "Steg zwischen microSD und Mini-USB", 1.5, "In Z gemessen"),
    ("MountLeft", "Linke Bohrungsmitten ab links", 1.5, "Beide linken Befestigungspunkte"),
    ("MountTop", "Linke obere Bohrung ab oben", 3, "Lochmitte"),
    ("MountBottom", "Linke untere Bohrung ab unten", 4.8, "Lochmitte"),
    ("MountRight", "Rechte Bohrung ab rechts", 20, "Lochmitte"),
    ("MountRightBottom", "Rechte Bohrung ab unten", 10.5, "Lochmitte"),
    ("MountHole", "Platine: Bohrungsdurchmesser", 2, "Nennmaß"),
    ("BossDiameter", "Platinendome: Außendurchmesser", 4.5, "Entwurfswert"),
    ("BossHeight", "Linke Platinendome: Höhe", 3, "Ab Platinenfront"),
    ("RightBossHeight", "Rechter Platinendom: Höhe", 1.5, "Ab Platinenfront, 0,5 mm unter Akku"),
    ("PilotHole", "Platinendome: Pilotbohrung", 1.6, "Auf Schrauben und Druck abstimmen"),
]

derived = [
    ("InnerW", "LCD-Tasche Breite", "LCDW + 2 * LCDPlay"),
    ("InnerH", "LCD-Tasche Höhe", "LCDH + 2 * LCDPlay"),
    ("OuterW", "Gehäuse Breite", "InnerW + 2 * Wall"),
    ("OuterH", "Gehäuse Höhe", "InnerH + 2 * Wall"),
    ("RearDepth", "Tiefe Rückrahmen", "LCDLip + LCDT + LCDGap"),
    ("BoardX", "Platine links", "(OuterW - BoardW) / 2"),
    ("BoardY", "Platine unten", "(OuterH - BoardH) / 2"),
    ("BoardZ", "Platine Rückseite", "RearDepth + BoardRearGap"),
    ("BoardFace", "Platine Vorderseite", "BoardZ + BoardT"),
    ("Depth", "Gehäuse Tiefe", "BoardFace + LensLength - LensOut"),
    ("LensX", "Linsenmitte X", "BoardX + BoardW - LensRight"),
    ("LensY", "Linsenmitte Y", "BoardY + BoardH - LensTop"),
    ("TopX", "Taste oben X", "BoardX + TopOffsetX"),
    ("TopZ", "Taste oben Z", "BoardFace + TopOffsetZ"),
    ("FrontX", "Taste vorn X", "BoardX + FrontOffsetX"),
    ("FrontY", "Taste vorn Y", "BoardY + FrontOffsetY"),
    ("FrontStemTip", "Fronttaste Druckstiftspitze Z", "Depth - Wall - FrontTravel - 1 mm - ButtonStem"),
    ("FrontBoardFace", "Fronttasterplatine Vorderseite Z", "FrontStemTip - FrontRestGap - FrontSwitchH"),
    ("FrontBoardBack", "Fronttasterplatine Rückseite Z", "FrontBoardFace - FrontBoardT"),
    ("UpperY", "Seitentaste oben Y", "BoardY + BoardH - SideTopGap - SideSwitchLength / 2"),
    ("LowerY", "Seitentaste unten Y", "BoardY + SideBottomGap + SideSwitchLength / 2"),
    ("SideZ", "Seitentasten Z", "BoardFace + SideOffsetZ"),
    ("OldRightY", "Alte rechte Kante in Seitenansicht", "( OuterH + OldCaseHeight ) / 2"),
    ("PortBottomZ", "Bündige Unterkante Mini-USB und Mini-HDMI", "BoardFace"),
    ("SdLeftY", "microSD linke Kante", "OldRightY - OldSdRightGap - SdW"),
    ("UsbLeftY", "Mini-USB linke Kante", "OldRightY - OldUsbRightGap - UsbLength"),
    ("BatteryX", "Akkufach X", "BoardX + BatteryLeft"),
    ("BatteryY", "Akkuunterkante Y", "BoardY + BatteryBottom"),
    ("BatteryBack", "Akkuschacht Z", "BoardFace + BatteryZ"),
    ("BatteryOpeningW", "Akkueinschub Breite", "BatteryW + 2 * BatteryPlay"),
    ("BatteryOpeningT", "Akkueinschub Tiefe", "BatteryT + 2 * BatteryPlay"),
    ("DoorLeft", "Deckel geschlossene linke Kante", "BatteryX - BatteryPlay - DoorOverlap"),
    ("DoorBack", "Deckel hintere Kante", "BatteryBack - BatteryPlay - DoorOverlap"),
    ("DoorW", "Deckel Breite", "BatteryOpeningW + 2 * DoorOverlap"),
    ("DoorD", "Deckel Tiefe", "BatteryOpeningT + 2 * DoorOverlap"),
    ("BatteryGuideLength", "Akkuführung Länge in Y", "BatteryY + BatteryH + BatteryPlay - Wall + 0.4 mm"),
    ("ContactX", "Kontaktblock linke Kante X", "BoardX + ContactLeft"),
    ("ContactRightX", "Kontaktblock rechte Kante X", "ContactX + ContactWidth"),
    ("ContactY", "Kontaktblock Unterkante Y", "BoardY + BoardH - ContactBottom"),
    ("ContactZ", "Kontaktblock äußerster Punkt Z", "BoardFace + ContactReach"),
    ("LensRearDiameter", "Hinterer Tubus: Ersatzdurchmesser", "2 * (LensX - BatteryX - BatteryW - LensBatteryGap)"),
    ("LensRearLength", "Hinterer Tubus: Ersatzlänge", "BatteryZ + BatteryT + BatteryPlay"),
    ("MountLeftX", "Linke Bohrungen X", "BoardX + MountLeft"),
    ("MountTopY", "Linke obere Bohrung Y", "BoardY + BoardH - MountTop"),
    ("MountBottomY", "Linke untere Bohrung Y", "BoardY + MountBottom"),
    ("MountRightX", "Rechte Bohrung X", "BoardX + BoardW - MountRight"),
    ("MountRightY", "Rechte Bohrung Y", "BoardY + MountRightBottom"),
]

for row, (alias, label, value, note) in enumerate(dimensions, 2):
    sheet.set(f"A{row}", label)
    sheet.set(f"B{row}", f"{value} mm")
    sheet.setAlias(f"B{row}", alias)
    sheet.set(f"C{row}", note)
for row, (alias, label, formula) in enumerate(derived, 2 + len(dimensions)):
    sheet.set(f"A{row}", label)
    sheet.set(f"B{row}", "=" + formula)
    sheet.setAlias(f"B{row}", alias)
    sheet.set(f"C{row}", "Berechnet")

aliases = {entry[0] for entry in dimensions + derived}


def assign(obj, prop, value):
    if isinstance(value, str):
        obj.setExpression(prop, expression(value))
    else:
        setattr(obj, prop, value)


def place(obj, position, axis=None):
    if axis is not None:
        obj.Placement = App.Placement(
            App.Vector(), App.Rotation(App.Vector(0, 0, 1), App.Vector(*axis))
        )
    for component, value in zip("xyz", position):
        obj.setExpression(
            f"Placement.Base.{component}",
            f"{value} mm" if isinstance(value, (int, float)) else expression(value),
        )


def expression(value):
    return " ".join(
        f"Dimensions.{token}" if token in aliases else token
        for token in value.split()
    )


def box(label, size, position):
    obj = doc.addObject("Part::Box", "Box")
    obj.Label = label
    for prop, value in zip(("Length", "Width", "Height"), size):
        assign(obj, prop, value)
    place(obj, position)
    return obj


def cylinder(label, radius, length, position, axis=(0, 0, 1)):
    obj = doc.addObject("Part::Cylinder", "Cylinder")
    obj.Label = label
    assign(obj, "Radius", radius)
    assign(obj, "Height", length)
    place(obj, position, axis)
    return obj


def fuse(label, *solids):
    obj = doc.addObject("Part::MultiFuse", "Union")
    obj.Label = label
    obj.Shapes = solids
    obj.Refine = True
    return obj


def cut(label, base, *tools):
    for tool in tools:
        obj = doc.addObject("Part::Cut", "Cut")
        obj.Label = "Abzug: " + tool.Label
        obj.Base = base
        obj.Tool = tool
        obj.Refine = True
        base = obj
    base.Label = label
    return base


body_stock = box("Vorderwanne außen", ("OuterW", "OuterH", "Depth - RearDepth"), (0, 0, "RearDepth"))
body_void = box("Innenraum", ("InnerW", "InnerH", "Depth - Wall - RearDepth + 1 mm"), ("Wall", "Wall", "RearDepth - 1 mm"))
lens_hole = cylinder("Objektivdurchlass", "LensHole / 2", "Wall + 2 mm", ("LensX", "LensY", "Depth - Wall - 1 mm"))
top_hole = cylinder("Führung oben", "3.5 mm + ButtonPlay", "Wall + 2 mm", ("TopX", "OuterH - Wall - 1 mm", "TopZ"), (0, 1, 0))
front_hole = cylinder("Führung vorn", "4.5 mm + ButtonPlay", "Wall + 2 mm", ("FrontX", "FrontY", "Depth - Wall - 1 mm"))

side_size = ("Wall + 2 mm", "5.5 mm + 2 * ButtonPlay", "2.5 mm + 2 * ButtonPlay")
side_holes = [
    box("Führung seitlich", side_size, (-1, f"{y} - 2.75 mm - ButtonPlay", "SideZ - 1.25 mm - ButtonPlay"))
    for y in ("UpperY", "LowerY")
]
speaker_pattern = [(0, 0)] + [(cos(i * pi / 3), sin(i * pi / 3)) for i in range(6)]
speaker_holes = [
    cylinder(
        "Schallöffnung linker Lautsprecher", "SpeakerHole / 2", "Wall + 4 mm",
        (-1, f"SpeakerY + ( {y:.12g} ) * SpeakerPitch", f"SpeakerZ + ( {z:.12g} ) * SpeakerPitch"),
        (1, 0, 0),
    )
    for y, z in speaker_pattern
]
service_hole = box(
    "Serviceöffnung (Position vorläufig)",
    ("Wall + 2 mm", "ServiceH", "ServiceW"),
    ("OuterW - Wall - 1 mm", "ServiceY - ServiceH / 2", "ServiceZ - ServiceW / 2"),
)
hdmi_hole = box(
    "Mini-HDMI 8,5 × 3",
    ("Wall + 2 mm", "HdmiLength", "HdmiWidth"),
    ("OuterW - Wall - 1 mm", "UsbLeftY - PortWeb - HdmiLength", "PortBottomZ"),
)
usb_hole = box(
    "Mini-USB 8,5 × 3,5",
    ("Wall + 2 mm", "UsbLength", "UsbWidth"),
    ("OuterW - Wall - 1 mm", "UsbLeftY", "PortBottomZ"),
)
sd_hole = box(
    "microSD Einschubschlitz 12 × 2",
    ("Wall + 2 mm", "SdW", "SdH"),
    ("OuterW - Wall - 1 mm", "SdLeftY", "PortBottomZ - SdWeb - SdH"),
)
battery_hole = box(
    "Akkueinschub",
    ("BatteryOpeningW", "DoorRimHeight + 2 mm", "BatteryOpeningT"),
    ("BatteryX - BatteryPlay", -1, "BatteryBack - BatteryPlay"),
)
shell = cut("Vorderwanne mit Durchbrüchen", body_stock, body_void, lens_hole, top_hole,
            front_hole, *side_holes, service_hole, usb_hole, hdmi_hole, sd_hole, battery_hole)

battery_guide_depth = "Depth - Wall + 0.4 mm - BatteryBack + BatteryPlay"
battery_left_guide = box(
    "Akkufach linke Führung",
    ("Wall", "BatteryGuideLength", battery_guide_depth),
    ("BatteryX - BatteryPlay - Wall", "Wall - 0.4 mm", "BatteryBack - BatteryPlay"),
)
battery_right_stock = box(
    "Akkufach rechte Führung Rohform",
    ("Wall", "BatteryGuideLength", battery_guide_depth),
    ("BatteryX + BatteryW + BatteryPlay", "Wall - 0.4 mm", "BatteryBack - BatteryPlay"),
)
lens_clearance = cylinder(
    "Objektivfreiraum an Akkuführung", "LensHole / 2", "LensLength",
    ("LensX", "LensY", "BoardFace"),
)
battery_partition = cut("Akkufach rechte Führung mit Objektivfreiraum", battery_right_stock, lens_clearance)

mount_centers = [
    ("links oben", "MountLeftX", "MountTopY", "BossHeight"),
    ("links unten", "MountLeftX", "MountBottomY", "BossHeight"),
    ("rechts unten", "MountRightX", "MountRightY", "RightBossHeight"),
]
mount_arms = [
    box(f"Auflage von linker Wand {name}",
        ("MountLeftX - Wall + 0.4 mm", "BossDiameter", height),
        ("Wall - 0.4 mm", f"{y} - BossDiameter / 2", "BoardFace"))
    for name, _, y, height in mount_centers[:2]
]
mount_arms.append(box(
    "Auflage von Bodenwand",
    ("BossDiameter", "MountRightY - Wall + 0.4 mm", "RightBossHeight"),
    ("MountRightX - BossDiameter / 2", "Wall - 0.4 mm", "BoardFace"),
))
mount_bosses = [
    cylinder(f"Platinendom {name}", "BossDiameter / 2", height, (x, y, "BoardFace"))
    for name, x, y, height in mount_centers
]
mount_pilots = [
    cylinder(f"Pilotbohrung {name}", "PilotHole / 2", f"{height} + 2 mm", (x, y, "BoardFace - 1 mm"))
    for name, x, y, height in mount_centers
]
front_holder = box(
    "Aufnahme der Fronttasterplatine",
    ("FrontBoardSize + 7 mm", "FrontBoardSize + 2.6 mm", "Depth - Wall + 0.4 mm - FrontBoardBack"),
    ("FrontX - FrontBoardSize / 2 - 3.5 mm", "FrontY - FrontBoardSize / 2 - 1.3 mm", "FrontBoardBack"),
)
front_board_pocket = box(
    "Tasche für Fronttasterplatine",
    ("FrontBoardSize + 0.4 mm", "FrontBoardSize + 0.4 mm", "FrontBoardT + 0.5 mm"),
    ("FrontX - FrontBoardSize / 2 - 0.2 mm", "FrontY - FrontBoardSize / 2 - 0.2 mm", "FrontBoardBack - 0.5 mm"),
)
front_button_clearance = cylinder(
    "Freiraum für Druckkappe und Druckkopf", "5.5 mm + ButtonPlay",
    "Depth - Wall - FrontBoardBack + 0.5 mm",
    ("FrontX", "FrontY", "FrontBoardBack - 0.5 mm"),
)
retainer_screw_x = ["FrontX - FrontBoardSize / 2 - 1.5 mm", "FrontX + FrontBoardSize / 2 + 1.5 mm"]
retainer_pilots = [
    cylinder("Pilotbohrung Fronttasterhalter", "PilotHole / 2", "4.5 mm",
             (x, "FrontY", "FrontBoardBack - 0.5 mm"))
    for x in retainer_screw_x
]
door_rim = box(
    "Verstärkung um den Akkudeckel",
    ("DoorW + DoorTravel + 2 * DoorPlay + 1.6 mm", "DoorRimHeight - 1.2 mm", "DoorD + 2 * DoorPlay + 1.6 mm"),
    ("DoorLeft - DoorPlay - 0.8 mm", 1.2, "DoorBack - DoorPlay - 0.8 mm"),
)
door_seat = box(
    "Bündiger Sitz mit Schiebeweg",
    ("DoorW + DoorTravel + 2 * DoorPlay", "DoorThickness + DoorPlay + 1 mm", "DoorD + 2 * DoorPlay"),
    ("DoorLeft - DoorPlay", -1, "DoorBack - DoorPlay"),
)
door_plate = box(
    "Akkudeckel Platte", ("DoorW", "DoorThickness", "DoorD"), ("DoorLeft", 0, "DoorBack"),
)
door_tabs = []
door_slots = []
for x in ("BatteryX + 5 mm", "BatteryX + BatteryW - 9 mm"):
    for z, tab_width in (
        ("DoorBack + DoorOverlap / 2 - 0.45 mm", 1.3),
        ("DoorBack + DoorD - DoorOverlap + 0.1 mm", 0.9),
    ):
        neck = box(
            "Akkudeckel Hakensteg", (1.2, "DoorRimHeight + DoorPlay + 0.9 mm - DoorThickness", tab_width),
            (x, "DoorThickness", z),
        )
        hook = box(
            "Akkudeckel Hakenkopf", ("DoorHookReach + 1.2 mm", 0.9, tab_width),
            (f"{x} - DoorHookReach", "DoorRimHeight + DoorPlay", z),
        )
        neck_slot = box(
            "Akkudeckel Führungsschlitz",
            ("DoorTravel + 1.2 mm + 2 * DoorPlay", "DoorRimHeight + 2 mm", f"{tab_width} mm + 2 * DoorPlay"),
            (f"{x} - DoorPlay", -1, f"{z} - DoorPlay"),
        )
        entry = box(
            "Einsetzöffnung für Haken",
            ("DoorHookReach + 1.2 mm + 2 * DoorPlay", "DoorRimHeight + 2 mm", f"{tab_width} mm + 2 * DoorPlay"),
            (f"{x} + DoorTravel - DoorHookReach - DoorPlay", -1, f"{z} - DoorPlay"),
        )
        door_tabs.extend((neck, hook))
        door_slots.extend((neck_slot, entry))
door_grip = box(
    "Schieberippe außen", (1, 0.8, 7),
    ("DoorLeft + DoorW - 4 mm", -0.6, "DoorBack + DoorD / 2 - 3.5 mm"),
)
door = fuse("03 Akkudeckel zum Schieben", door_plate, door_grip, *door_tabs)
body = cut("01 Vorderwanne mit Platinenauflagen und Akkufach",
           fuse("Wanne mit Akkuführung und Tasteraufnahme", shell, battery_left_guide,
                battery_partition, front_holder, door_rim, *mount_arms, *mount_bosses),
           *mount_pilots, front_board_pocket, front_button_clearance, front_hole, *retainer_pilots,
           battery_hole, door_seat, *door_slots, *speaker_holes)

retainer_stock = box(
    "Fronttaster-Halteplatte Rohform",
    ("FrontBoardSize + 7 mm", "FrontBoardSize + 0.4 mm", 1.6),
    ("FrontX - FrontBoardSize / 2 - 3.5 mm", "FrontY - FrontBoardSize / 2 - 0.2 mm", "FrontBoardBack - 1.6 mm"),
)
retainer_window = box(
    "Kabeldurchlass in Halteplatte",
    ("FrontBoardSize - 2 mm", "FrontBoardSize - 2 mm", 3),
    ("FrontX - FrontBoardSize / 2 + 1 mm", "FrontY - FrontBoardSize / 2 + 1 mm", "FrontBoardBack - 2 mm"),
)
retainer_holes = [
    cylinder("Schraubendurchlass", 1.1, 3, (x, "FrontY", "FrontBoardBack - 2 mm"))
    for x in retainer_screw_x
]
retainer = cut("08 Halteplatte Fronttaster", retainer_stock, retainer_window, *retainer_holes)

rear_stock = box("Rahmen außen", ("OuterW", "OuterH", "RearDepth"), (0, 0, 0))
lcd_pocket = box("LCD-Tasche", ("InnerW", "InnerH", "RearDepth - LCDLip + 1 mm"), ("Wall", "Wall", "LCDLip"))
lcd_window = box(
    "LCD-Fenster mit 1-mm-Auflage",
    ("LCDW - 2 * LCDLip", "LCDH - 2 * LCDLip", "LCDLip + 2 mm"),
    ("Wall + LCDPlay + LCDLip", "Wall + LCDPlay + LCDLip", -1),
)
rear = cut("02 LCD-Rückrahmen", rear_stock, lcd_pocket, lcd_window)

def round_button(label, radius, positions, axis, travel="ButtonTravel"):
    cap = cylinder("Druckkappe", radius, f"ButtonOut + Wall + {travel}", positions[0], axis)
    flange = cylinder("Halteflansch", radius + 1, 1, positions[1], axis)
    stem = cylinder("Druckstift", 1.45, "ButtonStem", positions[2], axis)
    return fuse(label, cap, flange, stem)


top_button = round_button(
    "04 Druckkappe oben", 3.5,
    [("TopX", y, "TopZ") for y in (
        "OuterH + ButtonOut", "OuterH - Wall - ButtonTravel", "OuterH - Wall - ButtonTravel - 1 mm")],
    (0, -1, 0),
)
front_button = round_button(
    "05 Druckkappe vorn", 4.5,
    [("FrontX", "FrontY", z) for z in (
        "Depth + ButtonOut", "Depth - Wall - FrontTravel", "Depth - Wall - FrontTravel - 1 mm")],
    (0, 0, -1),
    "FrontTravel",
)


def side_button(label, center_y):
    cap = box("Druckkappe", ("ButtonOut + Wall + ButtonTravel", 5.5, 2.5),
              ("-1 * ButtonOut", f"{center_y} - 2.75 mm", "SideZ - 1.25 mm"))
    flange = box("Halteflansch", (1, 7.5, 4.5),
                 ("Wall + ButtonTravel", f"{center_y} - 3.75 mm", "SideZ - 2.25 mm"))
    stem = box("Druckstift", ("ButtonStem", 3, 1),
               ("Wall + ButtonTravel + 1 mm", f"{center_y} - 1.5 mm", "SideZ - 0.5 mm"))
    return fuse(label, cap, flange, stem)


side_upper = side_button("06 Druckkappe Seite oben", "UpperY")
side_lower = side_button("07 Druckkappe Seite unten", "LowerY")
parts = [body, rear, door, top_button, front_button, side_upper, side_lower, retainer]

references = doc.addObject("App::DocumentObjectGroup", "References")
references.Label = "Referenzkörper"
board_blank = box("Platinengrundkörper", ("BoardW", "BoardH", "BoardT"), ("BoardX", "BoardY", "BoardZ"))
board_holes = [
    cylinder(f"Platinenbohrung {name}", "MountHole / 2", "BoardT + 2 mm", (x, y, "BoardZ - 1 mm"))
    for name, x, y, _ in mount_centers
]
board = cut("Hauptplatine 54 × 37,5 mit Befestigungsbohrungen", board_blank, *board_holes)
lcd = box("LCD im Originalbett", ("LCDW", "LCDH", "LCDT"), ("Wall + LCDPlay", "Wall + LCDPlay", "LCDLip"))
lens_rear = cylinder(
    "Hinterer Tubus (aus Akkuspalt geschätzt)",
    "LensRearDiameter / 2", "LensRearLength", ("LensX", "LensY", "BoardFace"),
)
lens_front = cylinder(
    "Vorderer Objektivteil (vereinfachte Hülle)",
    "LensDiameter / 2", "LensLength - LensRearLength",
    ("LensX", "LensY", "BoardFace + LensRearLength"),
)
lens = fuse("Objektiv (vereinfachte Stufenform)", lens_rear, lens_front)
battery = box("Akku in gemessener Einbaulage", ("BatteryW", "BatteryH", "BatteryT"), ("BatteryX", "BatteryY", "BatteryBack"))
contact_span = doc.addObject("Part::Line", "ContactSpan")
contact_span.Label = "Kontaktblock: gemessene Breite an den Bezugsflächen"
for prop, coordinate in (
    ("X1", "ContactX"), ("X2", "ContactRightX"),
    ("Y1", "ContactY"), ("Y2", "ContactY"),
    ("Z1", "ContactZ"), ("Z2", "ContactZ"),
):
    assign(contact_span, prop, coordinate)
front_board = box(
    "Fronttasterplatine (Dicke vorläufig)",
    ("FrontBoardSize", "FrontBoardSize", "FrontBoardT"),
    ("FrontX - FrontBoardSize / 2", "FrontY - FrontBoardSize / 2", "FrontBoardBack"),
)
front_switch = box(
    "Fronttaster (vereinfachte Hülle)",
    (6, 6, "FrontSwitchH"),
    ("FrontX - 3 mm", "FrontY - 3 mm", "FrontBoardFace"),
)
reference_solids = [board, lcd, lens, battery, front_board, front_switch]
references.Group = reference_solids + [contact_span]

doc.recompute()
for item in (board, front_board, retainer):
    bounds = item.Shape.BoundBox
    insertion_path = Part.makeBox(
        bounds.XLength, bounds.YLength, bounds.ZMax, App.Vector(bounds.XMin, bounds.YMin, 0),
    )
    assert body.Shape.common(insertion_path).Volume < 0.001, ("Einbau von hinten", item.Label)
for button_section in front_button.Shapes[:2]:
    bounds = button_section.Shape.BoundBox
    origin = App.Vector((bounds.XMin + bounds.XMax) / 2, (bounds.YMin + bounds.YMax) / 2, 0)
    insertion_path = Part.makeCylinder(button_section.Radius.Value, bounds.ZMax, origin)
    assert body.Shape.common(insertion_path).Volume < 0.001, "Einsetzen der Frontdruckkappe"
for opening in (hdmi_hole, usb_hole, sd_hole, service_hole, *speaker_holes):
    assert body.Shape.common(opening.Shape).Volume < 0.001, opening.Label
hdmi_bounds, usb_bounds, sd_bounds = [opening.Shape.BoundBox for opening in (hdmi_hole, usb_hole, sd_hole)]
assert abs(usb_bounds.YMin - hdmi_bounds.YMax - sheet.PortWeb.Value) < 0.001, "Steg HDMI/USB"
assert abs(usb_bounds.ZMin - sd_bounds.ZMax - sheet.SdWeb.Value) < 0.001, "Steg USB/microSD"
assert abs(usb_bounds.ZMin - hdmi_bounds.ZMin) < 0.001, "Bündige Unterkanten HDMI/USB"
assert abs(sheet.OldRightY.Value - sd_bounds.YMax - sheet.OldSdRightGap.Value) < 0.001, "Alter Rand zu microSD"
assert abs(sheet.OldRightY.Value - usb_bounds.YMax - sheet.OldUsbRightGap.Value) < 0.001, "Alter Rand zu Mini-USB"
battery_bounds = battery.Shape.BoundBox
battery_path = Part.makeBox(
    battery_bounds.XLength, battery_bounds.YMax, battery_bounds.ZLength,
    App.Vector(battery_bounds.XMin, 0, battery_bounds.ZMin),
)
assert body.Shape.common(battery_path).Volume < 0.001, "Einschub des Akkus von unten"
assert lens.Shape.common(battery_path).Volume < 0.001, "Einschub des Akkus am geschätzten Tubus"
door_obstacles = Part.makeCompound([body.Shape, retainer.Shape])
for fraction in (0.25, 0.5, 0.75, 1):
    moving_door = door.Shape.translated(App.Vector(sheet.DoorTravel.Value * fraction, 0, 0))
    assert door_obstacles.common(moving_door).Volume < 0.001, ("Akkudeckel Schiebeweg", fraction)
for offset in (1, 2, 3, 4):
    moving_door = door.Shape.translated(App.Vector(sheet.DoorTravel.Value, -offset, 0))
    assert door_obstacles.common(moving_door).Volume < 0.001, ("Akkudeckel Einsetzen", offset)
assert body.Shape.common(door.Shape.translated(App.Vector(0, -0.6, 0))).Volume > 0.001, "Akkudeckel rastet hinter Führung"
for item in parts + reference_solids:
    assert item.Shape.isValid() and len(item.Shape.Solids) == 1, item.Label
for index, first in enumerate(parts + reference_solids):
    for second in (parts + reference_solids)[index + 1:]:
        overlap = first.Shape.common(second.Shape).Volume
        assert overlap < 0.001, (first.Label, second.Label, overlap)

if App.GuiUp:
    import FreeCADGui as Gui

    for obj in doc.Objects:
        obj.Visibility = obj in parts + [lens, lcd, references]
    for obj in parts:
        obj.ViewObject.ShapeColor = (0.22, 0.31, 0.38) if obj in [body, rear] else (0.86, 0.53, 0.20)
    lens.ViewObject.ShapeColor = (0.12, 0.14, 0.17)
    lcd.ViewObject.ShapeColor = (0.08, 0.11, 0.16)
    view = Gui.activeDocument().activeView()
    view.viewAxonometric()
    view.fitAll()

doc.recompute()
doc.saveAs(str(HERE / "CT9000_Gehaeuse_V12.FCStd"))

test_parts = HERE / "Pruefteile"
test_parts.mkdir(exist_ok=True)
for source, filename in (
    (board, "CT9000_Platinen_Dummy.stl"),
    (battery, "CT9000_Akku_Dummy.stl"),
):
    shape = source.Shape.copy()
    bounds = shape.BoundBox
    shape.translate(App.Vector(-bounds.XMin, -bounds.YMin, -bounds.ZMin))
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02,
                                  AngularDeflection=0.12, Relative=False)
    assert mesh.isSolid(), filename
    mesh.write(str(test_parts / filename))

print(f"Geprüft: {len(parts)} einzelne Bauteile und ihre Einbauwege im Gehäuse.")

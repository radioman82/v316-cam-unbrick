"""Create the CT9000 replacement cap for the upper OK switch.

Run with FreeCAD's bundled Python, for example:
    "C:\\Program Files\\FreeCAD 1.1\\bin\\FreeCADCmd.exe" build_top_ok_button.py

The STL is intentionally oriented with the 8.5 x 8.5 mm visible face on Z=0.
That gives the tiny part a flat printing face; the offset switch pin points up.
"""
from pathlib import Path

import FreeCAD as App
import Mesh
import MeshPart
import Part


HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "OK_Button_Oben"
OUT_DIR.mkdir(exist_ok=True)

FCSTD_PATH = OUT_DIR / "CT9000_OK_Button_Oben_V4_8_5x8_5_13x13.FCStd"
STL_PATH = OUT_DIR / "CT9000_OK_Button_Oben_V4_8_5x8_5_13x13.stl"


def rounded_box(width, depth, height, radius, z=0.0):
    """Return a box with rounded vertical corners and exact outer dimensions."""
    x_bar = Part.makeBox(width - 2 * radius, depth, height, App.Vector(radius, 0, z))
    y_bar = Part.makeBox(width, depth - 2 * radius, height, App.Vector(0, radius, z))
    result = x_bar.fuse(y_bar)
    for x in (radius, width - radius):
        for y in (radius, depth - radius):
            result = result.fuse(
                Part.makeCylinder(radius, height, App.Vector(x, y, z))
            )
    return result.removeSplitter()


doc = App.newDocument("CT9000_OK_Button_Oben")
doc.Label = "CT9000 OK-Button oben"

sheet = doc.addObject("Spreadsheet::Sheet", "Dimensions")
sheet.Label = "Masse und Bezug (mm)"
sheet.set("A1", "Mass")
sheet.set("B1", "Wert")
sheet.set("C1", "Bezug")
sheet.setColumnWidth("A", 220)
sheet.setColumnWidth("B", 100)
sheet.setColumnWidth("C", 420)

dimensions = [
    ("Oeffnung", 9.8, "Gemessene quadratische Gehaeuseoeffnung"),
    ("Kappe", 8.5, "Sichtbare Kappe, korrigiert auf 8,5 x 8,5 mm"),
    ("Kappenhoehe", 2.0, "Hoehe der sichtbaren Kappe"),
    ("Flansch", 13.0, "Unterseite, gegenueber 11 x 11 mm je Seite 1 mm groesser"),
    ("Flanschhoehe", 0.5, "Reduziertes Mass; ergibt 2,5 mm Knopfhoehe ohne Druckstift"),
    ("StiftDurchmesser", 1.0, "Runder Druckstift / Bip"),
    ("Stifshoehe", 1.0, "Entwurfswert fuer den Druckweg; nach Passprobe anpassen"),
    ("TasterVonOben", 5.5, "Stiftmitte ab oberer Kante der 9,8-mm-Oeffnung"),
    ("TasterVonRechts", 4.5, "Stiftmitte ab rechter Kante der 9,8-mm-Oeffnung"),
    ("EckenradiusKappe", 0.6, "Kleine Rundung fuer angenehme Bedienung"),
    ("EckenradiusFlansch", 0.6, "Vermeidet scharfe Flanschecken"),
]

for row, (name, value, note) in enumerate(dimensions, start=2):
    sheet.set(f"A{row}", name)
    sheet.set(f"B{row}", f"{value} mm")
    sheet.setAlias(f"B{row}", name)
    sheet.set(f"C{row}", note)

# Coordinates use the lower-left corner of the 11 mm flange as origin.
# The 9.8 mm opening and the 8 mm cap are centred on that flange.
flange_size = 13.0
opening_size = 9.8
cap_size = 8.5
cap_height = 2.0
flange_height = 0.5
pin_diameter = 1.0
pin_height = 1.0

cap_xy = (flange_size - cap_size) / 2.0
opening_xy = (flange_size - opening_size) / 2.0
opening_right = opening_xy + opening_size
opening_top = opening_xy + opening_size
pin_x = opening_right - 4.5
pin_y = opening_top - 5.5

cap = rounded_box(cap_size, cap_size, cap_height, 0.6)
cap.translate(App.Vector(cap_xy, cap_xy, 0))
flange = rounded_box(flange_size, flange_size, flange_height, 0.6, cap_height)
pin = Part.makeCylinder(
    pin_diameter / 2.0,
    pin_height,
    App.Vector(pin_x, pin_y, cap_height + flange_height),
)

shape = cap.fuse(flange).fuse(pin).removeSplitter()
button = doc.addObject("PartDesign::Feature", "OK_Button_Oben")
button.Label = "OK-Button oben, 8,5 x 8,5 mm, Stift versetzt"
button.Shape = shape
button.addProperty("App::PropertyString", "Druckorientierung", "Fertigung")
button.Druckorientierung = "8,5 x 8,5 mm Sichtflaeche auf das Druckbett; Stift zeigt nach oben"
button.addProperty("App::PropertyVector", "Stiftversatz", "Kontrolle")
button.Stiftversatz = App.Vector(pin_x - flange_size / 2, pin_y - flange_size / 2, 0)
button.addProperty("App::PropertyString", "Stiftbezug", "Kontrolle")
button.Stiftbezug = "5,5 mm von oben und 4,5 mm von rechts der 9,8-mm-Oeffnung"

doc.recompute()
doc.saveAs(str(FCSTD_PATH))

mesh = MeshPart.meshFromShape(
    Shape=button.Shape,
    LinearDeflection=0.03,
    AngularDeflection=0.174533,
    Relative=False,
)
mesh.write(str(STL_PATH))
check_mesh = Mesh.Mesh(str(STL_PATH))

print(f"FCStd: {FCSTD_PATH}")
print(f"STL:   {STL_PATH}")
print(f"Solid: {button.Shape.isValid()} / solids={len(button.Shape.Solids)}")
print(f"Bounds: {button.Shape.BoundBox.XLength:.3f} x "
      f"{button.Shape.BoundBox.YLength:.3f} x {button.Shape.BoundBox.ZLength:.3f} mm")
print(f"STL mesh: facets={check_mesh.CountFacets}, solid={check_mesh.isSolid()}, "
      f"volume={check_mesh.Volume:.3f} mm3")
print(f"Pin centre: X={pin_x:.3f}, Y={pin_y:.3f} mm; "
      f"offset from centre=({pin_x - flange_size / 2:+.3f}, "
      f"{pin_y - flange_size / 2:+.3f}) mm")

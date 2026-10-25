"""Build sdvcam_autostart_stockmenu: Autostart + ORIGINAL-Dispatcher.

Basis: sdvcam_4tiles_autostart_v6 (Autostart-Hooks + Stubs, auf der Kamera bewaehrt)

Erkenntnis dieser Runde:
  Die Stock-Firmware HAT bereits einen vollstaendigen 4-Kachel-Dispatcher
  @ vaddr 0x5afe0. Er loggt "[fangjj]: function select value:%d" und bildet
  die Kachel auf den Bottom-Bar-Index ab:
        Kachel 0 (FOTO)   -> BottomBar 2
        Kachel 1 (VIDEO)  -> BottomBar 0
        Kachel 2 (STREAM) -> BottomBar 1
        Kachel 3 (SETUP)  -> BottomBar 3
  und ruft dann BottomBarFunctionProc(self, idx) @ 0x5aeac.

  Dieser Stock-Code war nur deshalb kaputt, weil Patch "Stream-String"
  (file 0x1f32a2) den LOG-FORMAT-STRING an vaddr 0x2032a2
  ("[fangjj]: function select value:") mit "/mnt/extsd/start_streaming.sh &"
  ueberschrieben hatte. Danach hat ein frueherer Patch (C) die ganze Funktion
  durch PostMsg(59,1) ersetzt — 59 ist aber MSG_BLUETOOTH_ENABLE, deshalb
  landete jede Kachel im selben Zustand ("immer Video").

  Zusaetzlich hatte Patch B (file 0x59852, 0x15 -> 0x0b) in der Tasten-Tabelle
  von FunctionSelectWindow::OnKeyEvent den Eintrag fuer die Vordertaste
  (Keycode 132) von "Close" auf "vorwaerts blaettern" umgebogen. Damit gab es
  KEINEN Weg mehr aus dem Menue heraus.

  => Beide Patches werden hier exakt auf Stock zurueckgesetzt:
       C  file 0x4afe0..0x4b02c  (76 B)  Stock-Dispatcher
       B  file 0x59852           (1 B)   0x0b -> 0x15  (Vordertaste = Zurueck)
       S  file 0x1f32a2..0x1f32c2 (32 B) Stock-Format-String

  Es bleiben nur die Autostart-Teile aus v6 aktiv:
       Patch D  file 0x4ba46   b.w 0x1f5130   (Show-Stub)
       Hook 1   file 0x5c0e8   b.w ...        (PreviewWindow::OnWindowLoaded)
       Hook 2   file 0x4ca28   b.w ...        (PreviewWindow::HandleMessage)
       Stubs    file 0x1e5130..0x1e51a4

Adressregel: vaddr = datei_offset + 0x10000
"""
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(HERE, "sdvcam_4tiles_autostart_v6")
STOCK_PATH = os.path.join(HERE, "sdvcam_v8")
OUT_PATH = os.path.join(HERE, "sdvcam_autostart_stockmenu")

BASE_MD5 = "7b08a865e4ae7c5dc107e5a4f684e363"
STOCK_MD5 = "ee7425e348fc3d35d09ff62fc405860a"

# (start, ende_exklusiv, beschreibung)
REVERTS = [
    (0x04AFE0, 0x04B02C, "Patch C: Stock-Dispatcher @ vaddr 0x5afe0"),
    (0x059852, 0x059853, "Patch B: Tasten-Tabelle, Vordertaste = Close"),
    (0x1F32A2, 0x1F32C2, "Stream-String -> Stock-Format-String @ vaddr 0x2032a2"),
]

with open(BASE_PATH, "rb") as f:
    base = f.read()
with open(STOCK_PATH, "rb") as f:
    stock = f.read()

assert len(base) == len(stock), "Laengen unterschiedlich!"
assert hashlib.md5(base).hexdigest() == BASE_MD5, "v6-MD5 stimmt nicht!"
assert hashlib.md5(stock).hexdigest() == STOCK_MD5, "v8-MD5 stimmt nicht!"

data = bytearray(base)

print("Rueckbau auf Stock:")
for start, end, desc in REVERTS:
    n = end - start
    assert data[start:end] != stock[start:end], f"{desc}: schon Stock?"
    data[start:end] = stock[start:end]
    print(f"  file 0x{start:06x}..0x{end:06x} ({n:3d} B)  {desc}")

# --- Gegenproben: Autostart-Teile muessen unveraendert sein ---
GUARDS = [
    (0x1E5130, 0x1E51A4, "Show-Stub + Autostart-Stub"),
    (0x04CA28, 0x04CA2C, "Hook 2 (HandleMessage)"),
    (0x05C0E8, 0x05C0EC, "Hook 1 (OnWindowLoaded)"),
    (0x04BA46, 0x04BA4A, "Patch D (Show-Stub-Aufruf)"),
]
for start, end, desc in GUARDS:
    assert data[start:end] == base[start:end], f"{desc} beschaedigt!"
print("\nAutostart-Teile unveraendert: OK")

assert len(data) == len(base), "Dateilaenge veraendert!"

# --- Differenz gegen Stock ausgeben: nur noch Autostart darf uebrig sein ---
print("\nVerbleibende Unterschiede gegenueber Stock (v8):")
i, n = 0, len(data)
allowed = [(0x04BA46, 0x04BA4A), (0x04CA28, 0x04CA2C),
           (0x05C0E8, 0x05C0EC), (0x1E5130, 0x1E51A4)]
while i < n:
    if data[i] != stock[i]:
        j = i
        while j < n and data[j] != stock[j]:
            j += 1
        ok = any(s <= i and j <= e for s, e in allowed)
        print(f"  file 0x{i:06x}..0x{j:06x} ({j-i:3d} B)  vaddr 0x{i+0x10000:06x}"
              f"  {'Autostart' if ok else '!!! UNERWARTET !!!'}")
        assert ok, f"Unerwartete Aenderung bei file 0x{i:06x}"
        i = j
    else:
        i += 1

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"\nWrote {OUT_PATH}")
print(f"MD5 = {hashlib.md5(data).hexdigest()}")

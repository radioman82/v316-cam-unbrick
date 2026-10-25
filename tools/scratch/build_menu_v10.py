"""Build sdvcam_menu_v10: v9 + PreviewWindow::Show() nach dem Schliessen des Menues.

Basis: sdvcam_autostart_stockmenu
       (MD5 be456a6f3ad22b54fcf86fb5ed13fa78 = Autostart + Original-Dispatcher)

Gegenueber v9 zusaetzlich (dispatch_v4.s):
    Nach FunctionSelectWindow->Close (0x697ac) wird PreviewWindow::Show()
    (self->vtable[0x6c]) aufgerufen. Close blendet das Menue nur aus und
    meldet dem Fenstermanager kein neues aktives Fenster; deshalb blieb
    "function window" das aktuelle Fenster (main.cpp:648) und die OK-Taste
    (keyCode 130) wurde geschluckt statt auszuloesen.

Adressregel: vaddr = datei_offset + 0x10000
"""
import hashlib
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(HERE, "sdvcam_autostart_stockmenu")
OUT_PATH = os.path.join(HERE, "sdvcam_menu_v10")
ASM = os.path.join(HERE, "dispatch_v4.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

BASE_MD5 = "be456a6f3ad22b54fcf86fb5ed13fa78"

DISPATCH_VADDR = 0x5AFE0
SLOT_END = 0x5B030              # danach beginnt die naechste Funktion
MAX_LEN = SLOT_END - DISPATCH_VADDR      # 80 B

STREAM_VADDR = 0x2032A2
STREAM_FILE = STREAM_VADDR - 0x10000
STREAM_LEN = 32
STREAM = b"/mnt/extsd/start_streaming.sh &\x00"


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout


obj = os.path.join(HERE, "dispatch_v4.o")
elf = os.path.join(HERE, "dispatch_v4.elf")
raw = os.path.join(HERE, "dispatch_v4.bin")
sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{raw}"')

with open(raw, "rb") as f:
    image = f.read()
assert len(image) > DISPATCH_VADDR, "Assembler-Ausgabe zu kurz"
code = image[DISPATCH_VADDR:]
assert len(code) <= MAX_LEN, f"Dispatcher zu lang: {len(code)} > {MAX_LEN}"
code = code.ljust(MAX_LEN, b"\x00")

with open(BASE_PATH, "rb") as f:
    data = bytearray(f.read())
base = bytes(data)
print(f"Basis: {len(data)} B, MD5 {hashlib.md5(base).hexdigest()}")
assert hashlib.md5(base).hexdigest() == BASE_MD5, "Basis-MD5 stimmt nicht!"

used = len(code.rstrip(b"\x00"))
print(f"Dispatcher: {used} B belegt von {MAX_LEN} B Platz")
assert used <= MAX_LEN, f"Dispatcher zu lang: {used} > {MAX_LEN}"

data[DISPATCH_VADDR - 0x10000:SLOT_END - 0x10000] = code

assert len(STREAM) <= STREAM_LEN, "Scriptname zu lang"
data[STREAM_FILE:STREAM_FILE + STREAM_LEN] = STREAM.ljust(STREAM_LEN, b"\x00")

assert len(data) == len(base), "Dateilaenge veraendert!"

# --- Gegenproben: Autostart-Teile unveraendert ---
GUARDS = [
    (0x1E5130, 0x1E51A4, "Show-Stub + Autostart-Stub"),
    (0x04CA28, 0x04CA2C, "Hook 2 (HandleMessage)"),
    (0x05C0E8, 0x05C0EC, "Hook 1 (OnWindowLoaded)"),
    (0x04BA46, 0x04BA4A, "Patch D (Show-Stub-Aufruf)"),
    (0x059852, 0x059853, "Vordertaste = Close (Stock)"),
]
for start, end, desc in GUARDS:
    assert data[start:end] == base[start:end], f"{desc} beschaedigt!"
print("Autostart-Teile und Vordertaste unveraendert: OK")

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"\nWrote {OUT_PATH}")
print(f"MD5 = {hashlib.md5(data).hexdigest()}")

# --- Disassemblierung zur Kontrolle ---
print("\nKontrolle (objdump):")
print(sh(f'"{TOOL}\\arm-none-eabi-objdump.exe" -D -b binary -marm -Mforce-thumb '
         f'--start-address=0x{DISPATCH_VADDR:x} --stop-address=0x{SLOT_END:x} "{raw}" '
         f'| sed -n "5,80p"'))

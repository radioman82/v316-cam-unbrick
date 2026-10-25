"""Build sdvcam_4tiles_menu_v7: korrigierter 4-Kachel-Dispatcher.

Basis: sdvcam_4tiles_autostart_v6 (Autostart + Patches B/C/D + Show-Stub)

Neu gegenueber v6:
  C  Dispatcher @ file 0x4afe0 (vaddr 0x5afe0) komplett ersetzt.
     Alt: PostMsg(59, 1) — 59 ist MSG_BLUETOOTH_ENABLE, deshalb tat
          jede Kachel dasselbe (immer Video).
     Neu: FOTO  -> ChangeWorkMode(self, 5, 0)   (mode_normal_pic)
          VIDEO -> ChangeWorkMode(self, 0, 0)   (mode_normal_rec)
          STREAM-> system("/mnt/extsd/start_streaming.sh &")
          SETUP -> BottomBarFunctionProc(self, 1)

Adressregel: vaddr = datei_offset + 0x10000
"""
import hashlib
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(HERE, "sdvcam_4tiles_autostart_v6")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_menu_v7")
ASM = os.path.join(HERE, "dispatch_v2.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

BASE_MD5 = "7b08a865e4ae7c5dc107e5a4f684e363"
DISPATCH_VADDR = 0x5AFE0
DISPATCH_FILE = DISPATCH_VADDR - 0x10000
SLOT_END = 0x5B030          # danach beginnt KeyFunctionProc
MAX_LEN = SLOT_END - DISPATCH_VADDR


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout


obj = os.path.join(HERE, "dispatch_v2.o")
elf = os.path.join(HERE, "dispatch_v2.elf")
raw = os.path.join(HERE, "dispatch_v2.bin")
sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{raw}"')

with open(raw, "rb") as f:
    image = f.read()
code = image[DISPATCH_VADDR:]
code = code.rstrip(b"\x00") or code

with open(BASE_PATH, "rb") as f:
    data = bytearray(f.read())
base = bytes(data)
print(f"Basis v6: {len(data)} B, MD5 {hashlib.md5(base).hexdigest()}")
assert hashlib.md5(base).hexdigest() == BASE_MD5, "v6-MD5 stimmt nicht!"

print(f"Neuer Dispatcher: {len(code)} B (Platz {MAX_LEN} B)")
assert len(code) <= MAX_LEN, f"Dispatcher zu lang: {len(code)} > {MAX_LEN}"

data[DISPATCH_FILE:DISPATCH_FILE + len(code)] = code
# Rest des Slots mit Null fuellen (alte Reste entfernen)
data[DISPATCH_FILE + len(code):DISPATCH_FILE + MAX_LEN] = b"\x00" * (MAX_LEN - len(code))

assert len(data) == len(base), "Dateilaenge veraendert!"

# Gegenprobe: Show-Stub und Autostart-Stub unveraendert
assert bytes(data[0x1E5130:0x1E513A]) == base[0x1E5130:0x1E513A], "Show-Stub beschaedigt!"
assert bytes(data[0x1E513C:0x1E51A4]) == base[0x1E513C:0x1E51A4], "Autostart-Stub beschaedigt!"
assert bytes(data[0x4CA28:0x4CA2C]) == base[0x4CA28:0x4CA2C], "Hook2 beschaedigt!"
assert bytes(data[0x5C0E8:0x5C0EC]) == base[0x5C0E8:0x5C0EC], "Hook1 beschaedigt!"
print("Show-Stub, Autostart-Stub und beide Hooks unveraendert: OK")

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"\nWrote {OUT_PATH}")
print(f"MD5 = {hashlib.md5(data).hexdigest()}")

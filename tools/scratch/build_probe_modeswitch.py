"""
Probe-Build: prueft, ob [self+0x114] im MSG_MODE_SWITCH_DONE-Zweig gueltig ist.

Basis: sdvcam_4tiles_final (Patches B/C/D + Show-Stub + Stream-String bereits enthalten)
Neu:   Patch E  @ vaddr 0x5caee (4 B)  -> b.w 0x1f5140
       Stub    @ vaddr 0x1f5140       -> Marker-Datei schreiben, Original ausfuehren

Adressregel (verifiziert): vaddr = datei_offset + 0x10000
"""
import hashlib, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL_PATH = os.path.join(HERE, "sdvcam_4tiles_final")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_probe2")
ASM = os.path.join(HERE, "probe_modeswitch.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

FINAL_MD5 = "5ce4e6c6f7125394b099dae940f124ed"


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout


obj = os.path.join(HERE, "probe_modeswitch.o")
elf = os.path.join(HERE, "probe_modeswitch.elf")
bin_ = os.path.join(HERE, "probe_modeswitch.bin")

sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{bin_}"')

with open(bin_, "rb") as f:
    stub = f.read()

with open(FINAL_PATH, "rb") as f:
    data = bytearray(f.read())
base = bytes(data)

print(f"final: {len(data)} bytes, MD5 {hashlib.md5(base).hexdigest()}")
assert hashlib.md5(base).hexdigest() == FINAL_MD5, "final MD5 mismatch!"

# --- Patches anwenden -------------------------------------------------------
PATCHES = [
    (0x5caee, 4, "E  MODE_SWITCH_DONE-Zweig -> Probe"),
    (0x1f5140, 100, "Probe-Stub in Code-Cave"),
]

for vaddr, ln, name in PATCHES:
    off = vaddr - 0x10000
    chunk = stub[vaddr:vaddr + ln]
    # Nur die tatsaechlich vorhandenen Bytes schreiben: ein kuerzerer Slice
    # in eine bytearray-Slice-Zuweisung wuerde die Datei verkleinern.
    data[off:off + len(chunk)] = chunk
    print(f"  {name}: vaddr 0x{vaddr:06x} -> file 0x{off:06x} ({len(chunk)} B)")
    print(f"      {chunk[:32].hex()}{'...' if len(chunk) > 32 else ''}")

assert len(data) == len(base), f"Laenge veraendert: {len(data)} != {len(base)}"

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"\nWrote {OUT_PATH}")
print(f"MD5 = {hashlib.md5(data).hexdigest()}")

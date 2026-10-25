"""
Autostart v4: 4-Kachel-Menue beim Booten automatisch anzeigen.

Basis: sdvcam_4tiles_final (Patches B/C/D + Show-Stub + Stream-String)
Neu:   Patch F @ vaddr 0x6c0e8 (4 B) -> b.w 0x1f513c
       Stub    @ vaddr 0x1f513c       -> Einmal-Flag, Original, Show()

Warum 0x6c0e8: Ende von PreviewWindow::OnWindowLoaded (preview.cpp).
Dort ist die UI fertig aufgebaut und [self+0x114] gueltig
(Probe-Build sdvcam_4tiles_probe3 -> /tmp/OL_OK).

Adressregel (verifiziert): vaddr = datei_offset + 0x10000
"""
import hashlib, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL_PATH = os.path.join(HERE, "sdvcam_4tiles_final")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_autostart_v4")
ASM = os.path.join(HERE, "autostart4_stub.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

FINAL_MD5 = "5ce4e6c6f7125394b099dae940f124ed"


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout


obj = os.path.join(HERE, "autostart4_stub.o")
elf = os.path.join(HERE, "autostart4_stub.elf")
bin_ = os.path.join(HERE, "autostart4_stub.bin")

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

PATCHES = [
    (0x5ca28, 4, "G  HandleMessage-Anfang -> hook2"),
    (0x6c0e8, 4, "F  OnWindowLoaded-Ende -> hook1"),
    (0x1f513c, 110, "Stubs in Code-Cave"),
]

for vaddr, ln, name in PATCHES:
    off = vaddr - 0x10000
    chunk = stub[vaddr:vaddr + ln]
    data[off:off + len(chunk)] = chunk
    print(f"  {name}: vaddr 0x{vaddr:06x} -> file 0x{off:06x} ({len(chunk)} B)")
    print(f"      {chunk[:32].hex()}{'...' if len(chunk) > 32 else ''}")

assert len(data) == len(base), f"Laenge veraendert: {len(data)} != {len(base)}"

# Show-Stub @0x1f5130 (10 B) darf nicht angetastet werden
assert bytes(data[0x1e5130:0x1e513a]) == bytes(base[0x1e5130:0x1e513a]), \
    "Show-Stub wurde ueberschrieben!"
print("  Show-Stub @0x1f5130 unveraendert: OK")

CAVE_END = 0x1f51a4
last = 0x1f513c + len(stub[0x1f513c:])
assert last <= CAVE_END, f"Stub zu lang: endet 0x{last:06x}, Cave endet 0x{CAVE_END:06x}"
print(f"  Stub endet 0x{last:06x}, Cave-Ende 0x{CAVE_END:06x}: OK ({CAVE_END - last} B Reserve)")

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"\nWrote {OUT_PATH}")
print(f"MD5 = {hashlib.md5(data).hexdigest()}")

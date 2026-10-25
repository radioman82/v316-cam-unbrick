"""Autostart-Patch auf ein sdvcam-Binary anwenden.

Setzt zwei Hooks (HandleMessage-Anfang + OnWindowLoaded-Ende) und kopiert den
Stub in die Code-Cave bei 0x1f513c. Dadurch erscheint das 4-Kachel-Menue
direkt beim Booten.

Basis muss ein Build sein, der den Show-Stub @0x1f5130 bereits enthaelt
(z. B. sdvcam_4tiles_final).

usage: python patch_autostart.py <basis_binary> <ziel_binary>
       python patch_autostart.py <basis_binary> <ziel_binary> --force

Adressregel (verifiziert): vaddr = datei_offset + 0x10000
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASM = os.path.join(HERE, "patches", "autostart.s")
TOOL = os.environ.get(
    "ARM_TOOLCHAIN",
    r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin",
)

# vaddr, Laenge, Bezeichnung
PATCHES = [
    (0x5CA28, 4, "G  HandleMessage-Anfang -> hook2"),
    (0x6C0E8, 4, "F  OnWindowLoaded-Ende -> hook1"),
    (0x1F513C, 110, "Stubs in Code-Cave"),
]

SHOW_STUB = (0x1F5130, 0x1F513A)   # darf nicht angetastet werden
CAVE_END = 0x1F51A4                # ab hier echte Strings
VADDR_BASE = 0x10000               # R-Segment


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout


def build_stub():
    obj = os.path.join(HERE, "_autostart.o")
    elf = os.path.join(HERE, "_autostart.elf")
    raw = os.path.join(HERE, "_autostart.bin")
    sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
    sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
    sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{raw}"')
    with open(raw, "rb") as f:
        data = f.read()
    for p in (obj, elf, raw):
        os.unlink(p)
    return data


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    src, dst = sys.argv[1], sys.argv[2]
    force = "--force" in sys.argv

    stub = build_stub()
    with open(src, "rb") as f:
        data = bytearray(f.read())
    base = bytes(data)
    print(f"Basis: {src} ({len(data)} B, MD5 {hashlib.md5(base).hexdigest()})")

    if bytes(data[0x1E5130:0x1E513A]) == b"\x00" * 10 and not force:
        raise SystemExit(
            "Der Show-Stub @0x1f5130 fehlt im Basis-Binary.\n"
            "Erst Patches B/C/D + Show-Stub anwenden (sdvcam_4tiles_final).\n"
            "Mit --force trotzdem fortfahren."
        )

    for vaddr, ln, name in PATCHES:
        off = vaddr - VADDR_BASE
        chunk = stub[vaddr:vaddr + ln]
        data[off:off + len(chunk)] = chunk
        print(f"  {name}: vaddr 0x{vaddr:06x} -> file 0x{off:06x} ({len(chunk)} B)")
        print(f"      {chunk[:32].hex()}{'...' if len(chunk) > 32 else ''}")

    assert len(data) == len(base), "Dateilaenge veraendert!"

    if not force:
        assert bytes(data[0x1E5130:0x1E513A]) == base[0x1E5130:0x1E513A], \
            "Show-Stub wurde ueberschrieben!"
        print("  Show-Stub @0x1f5130 unveraendert: OK")

    last = 0x1F513C + len(stub[0x1F513C:])
    assert last <= CAVE_END, \
        f"Stub zu lang: endet 0x{last:06x}, Cave endet 0x{CAVE_END:06x}"
    print(f"  Stub endet 0x{last:06x}, Cave-Ende 0x{CAVE_END:06x}: "
          f"OK ({CAVE_END - last} B Reserve)")

    with open(dst, "wb") as f:
        f.write(data)
    print(f"\nWrote {dst}")
    print(f"MD5 = {hashlib.md5(data).hexdigest()}")


if __name__ == "__main__":
    main()

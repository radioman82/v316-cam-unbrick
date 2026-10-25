"""
Hilfsskript: Strings im sdvcam-Binary finden und Code-Referenzen (Literal-Pools) darauf.
Adressregel: vaddr = datei_offset + 0x10000
"""
import struct, sys, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "sdvcam_v8")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

with open(BIN, "rb") as f:
    DATA = f.read()

def find_string(needle: bytes):
    """Alle Vorkommen eines Strings: (datei_offset, vaddr)"""
    out = []
    pos = 0
    while True:
        pos = DATA.find(needle, pos)
        if pos < 0:
            break
        out.append((pos, pos + 0x10000))
        pos += 1
    return out

def find_xrefs(vaddr: int):
    """Sucht 4-Byte-Little-Endian-Referenzen auf eine vaddr (Literal-Pool)."""
    hits = []
    for val in (vaddr, vaddr | 1):
        pat = struct.pack("<I", val)
        pos = 0
        while True:
            pos = DATA.find(pat, pos)
            if pos < 0:
                break
            hits.append((pos, pos + 0x10000, val))
            pos += 1
    return hits

def disasm(start, stop):
    cmd = [os.path.join(TOOL, "arm-none-eabi-objdump.exe"), "-d",
           "--adjust-vma=0x10000",
           f"--start-address=0x{start:x}", f"--stop-address=0x{stop:x}", BIN]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout

if __name__ == "__main__":
    needle = sys.argv[1].encode()
    print(f"Suche String: {needle!r}")
    strs = find_string(needle)
    for foff, va in strs:
        print(f"  file 0x{foff:06x}  vaddr 0x{va:06x}")
        for xf, xva, val in find_xrefs(va):
            print(f"     xref -> file 0x{xf:06x}  vaddr 0x{xva:06x}  (val 0x{val:x})")

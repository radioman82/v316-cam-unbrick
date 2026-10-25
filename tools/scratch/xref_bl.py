"""Findet Thumb-2 BL/BLX-Aufrufer einer Zieladresse in einem Rohbinary.

Adressen werden als vaddr angegeben (vaddr = datei_offset + 0x10000).

usage: python xref_bl.py <ziel_vaddr> [<ziel_vaddr> ...]
       (nutzt immer sdvcam_v8 im selben Verzeichnis)
"""
import os
import struct
import sys

BASE = 0x10000
HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "sdvcam_v8")


def decode_bl(hw1, hw2):
    if (hw1 & 0xF800) != 0xF000:
        return None
    if (hw2 & 0xD000) != 0xD000:
        return None
    s = (hw1 >> 10) & 1
    imm10 = hw1 & 0x3FF
    j1 = (hw2 >> 13) & 1
    j2 = (hw2 >> 11) & 1
    i1 = (~(j1 ^ s)) & 1
    i2 = (~(j2 ^ s)) & 1
    imm = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | ((hw2 & 0x7FF) << 1)
    if s:
        imm -= 1 << 25
    blx = ((hw2 >> 12) & 1) == 0
    return imm, blx


def main():
    targets = {int(t, 0): [] for t in sys.argv[1:]}
    with open(BIN, "rb") as f:
        d = f.read()

    for off in range(0, len(d) - 4, 2):
        hw1, hw2 = struct.unpack_from("<HH", d, off)
        r = decode_bl(hw1, hw2)
        if r is None:
            continue
        imm, blx = r
        addr = off + BASE
        target = addr + 4 + imm
        if target in targets:
            targets[target].append((addr, "BLX" if blx else "BL"))

    for t, hits in targets.items():
        print(f"=== Ziel vaddr 0x{t:06x}: {len(hits)} Aufrufer")
        for addr, kind in hits:
            print(f"    {kind} @ vaddr 0x{addr:06x}  (Datei 0x{addr - BASE:06x})")


if __name__ == "__main__":
    main()

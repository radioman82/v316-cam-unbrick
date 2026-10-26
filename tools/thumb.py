"""Thumb-2 Branch-Kodierung (B.W / BL) und Verifikation gegen bekannte Stellen.

usage:
  python thumb.py enc  <src_addr> <dst_addr> [bl|b]
  python thumb.py test
"""


def _enc(src, dst, bl):
    off = dst - (src + 4)
    if not (-0x1000000 <= off <= 0xFFFFFE):
        raise ValueError("Ziel ausserhalb der Reichweite")
    imm32 = off & 0x1FFFFFF          # 25 Bit
    s = (imm32 >> 24) & 1
    i1 = (imm32 >> 23) & 1
    i2 = (imm32 >> 22) & 1
    imm10 = (imm32 >> 12) & 0x3FF
    imm11 = (imm32 >> 1) & 0x7FF
    j1 = (~i1 & 1) ^ s
    j2 = (~i2 & 1) ^ s
    w = 0xF000 | (s << 10) | imm10
    w2 = (0b11 << 14) | (j1 << 13) | (0b1 << 12) | (j2 << 11) | imm11
    if bl:
        w2 |= 0b01 << 14   # BL: bits15:14 = 11 und bit14... siehe unten
    return w, w2


def enc_bl(src, dst):
    """32-Bit BL (Thumb-2). Rueckgabe als little-endian Bytes."""
    off = dst - (src + 4)
    imm32 = off & 0x1FFFFFF
    s = (imm32 >> 24) & 1
    i1 = (imm32 >> 23) & 1
    i2 = (imm32 >> 22) & 1
    imm10 = (imm32 >> 12) & 0x3FF
    imm11 = (imm32 >> 1) & 0x7FF
    j1 = ((i1 ^ 1) & 1) ^ s
    j2 = ((i2 ^ 1) & 1) ^ s
    hw1 = 0xF000 | (s << 10) | imm10
    hw2 = 0xD000 | (j1 << 13) | (j2 << 11) | imm11
    return hw1.to_bytes(2, "little") + hw2.to_bytes(2, "little")


def enc_bw(src, dst):
    """32-Bit B.W (Thumb-2, unbedingt)."""
    off = dst - (src + 4)
    imm32 = off & 0x1FFFFFF
    s = (imm32 >> 24) & 1
    i1 = (imm32 >> 23) & 1
    i2 = (imm32 >> 22) & 1
    imm10 = (imm32 >> 12) & 0x3FF
    imm11 = (imm32 >> 1) & 0x7FF
    j1 = ((i1 ^ 1) & 1) ^ s
    j2 = ((i2 ^ 1) & 1) ^ s
    hw1 = 0xF000 | (s << 10) | imm10
    hw2 = 0x8000 | (j1 << 13) | 0x1000 | (j2 << 11) | imm11
    return hw1.to_bytes(2, "little") + hw2.to_bytes(2, "little")


def _selftest():
    # bekannte Stellen aus sdvcam_v8
    cases = [
        ("b.w 0x5b030 @0x5ba68", enc_bw(0x5ba68, 0x5b030), "e2bae2f7"[0:0] or None),
    ]
    d = open("sdvcam_v8", "rb").read()
    ok = True
    for name, enc, _ in cases:
        real = d[0x5ba68 - 0x10000:0x5ba68 - 0x10000 + 4]
        print(name, "erzeugt:", enc.hex(" "), " echt:", real.hex(" "))
        ok &= enc == real
    # BL 0x22684 @0x5b8b0
    enc = enc_bl(0x5b8b0, 0x22684)
    real = d[0x5b8b0 - 0x10000:0x5b8b0 - 0x10000 + 4]
    print("bl 0x22684 @0x5b8b0  erzeugt:", enc.hex(" "), " echt:", real.hex(" "))
    ok &= enc == real
    # BL 0x6264c @0x629b8
    enc = enc_bl(0x629b8, 0x6264c)
    real = d[0x629b8 - 0x10000:0x629b8 - 0x10000 + 4]
    print("bl 0x6264c @0x629b8  erzeugt:", enc.hex(" "), " echt:", real.hex(" "))
    ok &= enc == real
    print("SELFTEST", "OK" if ok else "FEHLGESCHLAGEN")


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == "test":
        _selftest()
    elif len(sys.argv) >= 4 and sys.argv[1] == "enc":
        src, dst = int(sys.argv[2], 0), int(sys.argv[3], 0)
        kind = sys.argv[4] if len(sys.argv) > 4 else "bw"
        f = {"bw": enc_bw, "bl": enc_bl}[kind]
        print(f"{kind} {hex(src)} -> {hex(dst)}: {f(src, dst).hex(' ')}")
    else:
        print(__doc__)

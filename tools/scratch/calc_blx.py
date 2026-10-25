import capstone

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

# From Thumb to ARM:
# blx <target>
# target = 0x1c94c
# pc = (address + 4) & ~3
def encode_thumb_blx(addr, target):
    pc = (addr + 4) & ~3
    diff = target - pc
    sign = 1 if diff < 0 else 0
    imm32 = diff & 0x1ffffff
    s = (imm32 >> 24) & 1
    i1 = (imm32 >> 23) & 1
    i2 = (imm32 >> 22) & 1
    imm10 = (imm32 >> 12) & 0x3ff
    imm11 = (imm32 >> 1) & 0x7ff
    j1 = (~i1 ^ s) & 1
    j2 = (~i2 ^ s) & 1
    hw1 = 0xf000 | (s << 10) | imm10
    hw2 = 0xe800 | (j1 << 13) | (j2 << 11) | imm11
    import struct
    return struct.pack("<HH", hw1, hw2)

addr = 0x5ba52
code = encode_thumb_blx(addr, 0x1c94c)
for insn in md.disasm(code, addr):
    print(f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

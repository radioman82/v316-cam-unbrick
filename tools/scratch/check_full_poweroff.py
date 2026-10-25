import capstone, struct

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

# pc for ldr at 0x5ba4e: (0x5ba4e + 4) & ~3 = 0x5ba50
# target word at 0x5ba60: 0x5ba60 - 0x5ba50 = 0x10 = 16 bytes -> 16 / 4 = 4
# ldr r0, [pc, #16] -> 0x4804
ldr_r0 = bytes([0x04, 0x48]) # ldr r0, [pc, #16]
nop    = bytes([0x00, 0xbf]) # nop (to align blx at 0x5ba52)

# blx 0x1c94c at 0x5ba52
def encode_thumb_blx(addr, target):
    pc = (addr + 4) & ~3
    diff = target - pc
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
    return struct.pack("<HH", hw1, hw2)

blx_sys = encode_thumb_blx(0x5ba52, 0x1c94c)

# b 0x5ba6c from 0x5ba56:
# 0x5ba6c - (0x5ba56 + 4) = 0x5ba6c - 0x5ba5a = 0x12 = 18 bytes -> 18 / 2 = 9 -> 0xe009
b_exit = bytes([0x09, 0xe0])
nops = bytes([0x00, 0xbf, 0x00, 0xbf, 0x00, 0xbf]) # 6 bytes
ptr_word = struct.pack("<I", 0x001ff54f) # "poweroff -f"

full_seq = ldr_r0 + nop + blx_sys + b_exit + nops + ptr_word

print("=== DISASSEMBLING FULL POWEROFF HANDLER ===")
for insn in md.disasm(full_seq, 0x5ba4e):
    print(f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

print("Total length:", len(full_seq))

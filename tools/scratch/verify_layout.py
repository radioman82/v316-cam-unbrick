import capstone, struct

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

ldr_r0 = bytes([0x04, 0x48]) # ldr r0, [pc, #16] at 0x5ba4e -> loads from 0x5ba60!
nop    = bytes([0x00, 0xbf]) # 0x5ba50

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

blx_sys = encode_thumb_blx(0x5ba52, 0x1c94c) # 0x5ba52..0x5ba56

# b #0x5ba6c from 0x5ba56:
# 0x5ba6c - (0x5ba56 + 4) = 0x12 -> 0xe009
b_exit = bytes([0x09, 0xe0]) # 0x5ba56..0x5ba58
nops8  = bytes([0x00, 0xbf] * 4) # 0x5ba58..0x5ba60
ptr_word = struct.pack("<I", 0x001ff54f) # 0x5ba60..0x5ba64
nops4 = bytes([0x00, 0xbf] * 2) # 0x5ba64..0x5ba68

code_block = ldr_r0 + nop + blx_sys + b_exit + nops8 + ptr_word + nops4
print("Length:", len(code_block))

# Disassemble up to 0x5ba60
for insn in md.disasm(code_block[:0x12], 0x5ba4e):
    print(f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

# Check word at 0x5ba60
w = struct.unpack("<I", code_block[0x12:0x16])[0]
print(f"Word at 0x5ba60: {hex(w)}")

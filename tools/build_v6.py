import capstone, struct

with open('d:/v316cm/sdvcam_v5', 'rb') as f:
    data = bytearray(f.read())

# Layout the poweroff block at 0x5ba4e (file offset 0x4ba4e)
# 26 bytes from 0x4ba4e to 0x4ba68
ldr_r0 = bytes([0x04, 0x48]) # ldr r0, [pc, #16] at 0x5ba4e -> loads from 0x5ba60
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
b_exit = bytes([0x09, 0xe0]) # b #0x5ba6c at 0x5ba56..0x5ba58
nops8  = bytes([0x00, 0xbf] * 4) # 0x5ba58..0x5ba60
ptr_word = struct.pack("<I", 0x001ff54f) # 0x5ba60..0x5ba64 ("poweroff -f")
nops4 = bytes([0x00, 0xbf] * 2) # 0x5ba64..0x5ba68

code_block = ldr_r0 + nop + blx_sys + b_exit + nops8 + ptr_word + nops4
assert len(code_block) == 26

data[0x4ba4e:0x4ba4e+26] = code_block

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
print("=== VERIFYING POWEROFF DISASSEMBLY IN sdvcam_v6 ===")
for insn in md.disasm(data[0x4ba4a:0x4ba70], 0x5ba4a):
    print(f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

with open('d:/v316cm/sdvcam_v6', 'wb') as f:
    f.write(data)
print("Saved d:/v316cm/sdvcam_v6, size:", len(data))

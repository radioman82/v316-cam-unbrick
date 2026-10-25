import struct, capstone

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

# At 0x5c90e, it called 0x69de8 (constructor of FunctionSelectWindow)
# Let us disassemble 0x69de8 to find where vtable is assigned!
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

start = 0x69de8 - 0x10000
code = data[start:start+0x50]
for insn in md.disasm(code, 0x69de8):
    print(f'0x{insn.address:x}: {insn.mnemonic} {insn.op_str}')

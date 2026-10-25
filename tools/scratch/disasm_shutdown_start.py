import capstone

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

start = 0x6c674 - 0x10000
code = data[start:start+0x80]
for insn in md.disasm(code, 0x6c674):
    print(f'0x{insn.address:x}: {insn.mnemonic} {insn.op_str}')

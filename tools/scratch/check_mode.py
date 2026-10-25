import capstone

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

md_arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
md_thumb = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

start = 0x50180 - 0x10000
code = data[start:start+0xc0]

print("=== ARM MODE ===")
for insn in md_arm.disasm(code, 0x50180):
    print(f'0x{insn.address:x}: {insn.mnemonic} {insn.op_str}')

print("=== THUMB MODE ===")
for insn in md_thumb.disasm(code, 0x50180):
    print(f'0x{insn.address:x}: {insn.mnemonic} {insn.op_str}')

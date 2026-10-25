import capstone

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

md_arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

start = 0x1c94c - 0x10000
code = data[start:start+0x20]

print("=== PLT 0x1c94c ===")
for insn in md_arm.disasm(code, 0x1c94c):
    print(f'0x{insn.address:x}: {insn.mnemonic} {insn.op_str}')

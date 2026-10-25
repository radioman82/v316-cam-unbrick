import capstone

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

for off in range(0, len(data)-4, 2):
    # disassemble 4 bytes
    for insn in md.disasm(data[off:off+4], off + 0x10000):
        if '0x114' in insn.op_str and 'str' in insn.mnemonic:
            print(f'0x{insn.address:x}: {insn.mnemonic} {insn.op_str}')

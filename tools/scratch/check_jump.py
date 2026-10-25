import capstone

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
b16 = bytes([0x3e, 0xe0])
for insn in md.disasm(b16, 0x5b034):
    print(f'0x{insn.address:x}: {insn.mnemonic} {insn.op_str}')

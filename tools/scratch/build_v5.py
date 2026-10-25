import capstone

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = bytearray(f.read())

# Patch 1: Bypass USBModeWindow
data[0x3ed64:0x3ed68] = bytes([0x01, 0xe0, 0x00, 0xbf])

# Patch 2: Bypass Preview is_hidden drop
data[0x472ba:0x472bc] = bytes([0x09, 0xe0])

# Patch 3: In KeyFunctionProc, direct jump to open FunctionSelectWindow at 0x5b0b4
data[0x4b034:0x4b036] = bytes([0x3e, 0xe0])

# Patch 4: Preview key handler, bypass standby drop at 0x5b996
data[0x4b996:0x4b998] = bytes([0x07, 0xe0])

# Patch 5: Preview key handler, always route to switch table at 0x5b9b2
data[0x4b9b2:0x4b9b4] = bytes([0x08, 0xe0])

# Patch 6: Side UP (0x87) -> 0x5ba60 -> KeyFunctionProc
data[0x4b9d0:0x4b9d4] = bytes([0x46, 0xd0, 0x00, 0xbf])

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

print("=== VERIFYING PATCHES ===")
print("--- 1. USB Mode Bypass ---")
for insn in md.disasm(data[0x3ed60:0x3ed70], 0x4ed60):
    print(f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

print("--- 2. IsVisible Bypass ---")
for insn in md.disasm(data[0x472b8:0x472c2], 0x572b8):
    print(f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

print("--- 3. KeyFunctionProc Direct Open ---")
for insn in md.disasm(data[0x4b030:0x4b03c], 0x5b030):
    print(f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

print("--- 4, 5, 6. Preview Key Handler ---")
for insn in md.disasm(data[0x4b994:0x4b9dc], 0x5b994):
    print(f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")

with open('d:/v316cm/sdvcam_v5', 'wb') as f:
    f.write(data)
print("Saved d:/v316cm/sdvcam_v5 successfully, size:", len(data))

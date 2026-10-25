import capstone

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

# Target: at 0x5ba4e:
# ldr r0, [pc, #0x14] (pc is 0x5ba52 -> align 4 is 0x5ba50? Wait: in Thumb: PC = (address + 4) & ~3)
# (0x5ba4e + 4) & ~3 = 0x5ba50
# To load from 0x5ba64: 0x5ba64 - 0x5ba50 = 0x14 = 20 bytes -> 20 / 4 = 5 -> ldr r0, [pc, #20] = 0x4805!
# blx 0x1c94c from 0x5ba50:
# blx to ARM address:
# Let us check opcode for blx 0x1c94c from 0x5ba50:
# In Thumb: blx <arm_addr>
# displacement = 0x1c94c - ((0x5ba50 + 4) & ~3) = 0x1c94c - 0x5ba54 = -0x3f108
# Let us compute the exact branch with capstone/keystone or python
with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    orig = f.read()

# Let us find another call to 0x1c94c in the binary and inspect its opcode!
target_blx = 0x1c94c
for off in range(0, len(orig)-4, 2):
    addr = off + 0x10000
    insns = list(md.disasm(orig[off:off+4], addr))
    for insn in insns:
        if insn.mnemonic == "blx" and "1c94c" in insn.op_str:
            print(f"Found blx #0x1c94c at {hex(insn.address)}: {orig[off:off+4].hex()}")
            break

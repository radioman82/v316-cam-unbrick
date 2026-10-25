import subprocess

orig_p = r"d:\v316cm\Firmware\firm\versuch6\_full_img_verbose.fex.extracted\squashfs-root\usr\bin\sdvcam"
with open(orig_p, "rb") as f:
    data = bytearray(f.read())

off = 0x4b9d0
orig_bytes = data[off:off+4]
print("Original bytes at 0x4b9d0:", orig_bytes.hex())

# Replace 'beq.w 5bbf0' with 'beq.w 5b030'
# 5b030 is KeyFunctionProc (opens FunctionSelectWindow)
# Little endian: 3f f4 fe af
patch_bytes = bytes.fromhex("3ff4feaf")
data[off:off+4] = patch_bytes

out_p = r"d:\v316cm\sdvcam_menu_patch"
with open(out_p, "wb") as f:
    f.write(data)

print(f"Patched binary written to {out_p}")

# Disassemble patched section to verify
cmd = [
    r'C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin\arm-none-eabi-objdump.EXE',
    '-d', '--start-address=0x5b9c0', '--stop-address=0x5b9f0', out_p
]
out = subprocess.check_output(cmd).decode()
print("\nDisassembly of patched area:")
print(out)

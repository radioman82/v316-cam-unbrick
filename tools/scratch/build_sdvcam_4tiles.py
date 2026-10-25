import os, hashlib, subprocess

V8_PATH = r"d:\v316cm\sdvcam_v8"
OUT_PATH = r"d:\v316cm\sdvcam_4tiles"

with open(V8_PATH, "rb") as f:
    data = bytearray(f.read())

print(f"Loaded sdvcam_v8: {len(data)} bytes, MD5: {hashlib.md5(data).hexdigest()}")

# 1. Front button inside FunctionSelectWindow advances tile
# Offset 0x59852: change 0x15 -> 0x0b
print(f"Byte at 0x59852 before: {hex(data[0x59852])}")
data[0x59852] = 0x0b

# 2. Front button in PreviewWindow (short press) opens FunctionSelectWindow
# Offset 0x4b9e6: 6 bytes -> mov r0, r4; b.w 0x5b030
with open(r"d:\v316cm\test_branch_fproc.elf", "rb") as f:
    b_elf = f.read()
b_pos = b_elf.find(b"\x20\x46\xff\xf7\x22\xbb")
assert b_pos != -1, "Branch pattern not found in test_branch_fproc.elf"
branch_bytes = b_elf[b_pos : b_pos + 6]
data[0x4b9e6 : 0x4b9e6 + 6] = branch_bytes

# 3. FunctionChangeProc 4-Tile Action Dispatcher at 0x4afe0
with open(r"d:\v316cm\asm_patch.elf", "rb") as f:
    p_elf = f.read()
p_pos = p_elf.find(b"\x30\xb5\x04\x46\x15\x46")
assert p_pos != -1, "Dispatcher pattern not found in asm_patch.elf"
disp_bytes = p_elf[p_pos : p_pos + 76]
data[0x4afe0 : 0x4afe0 + len(disp_bytes)] = disp_bytes

# 4. Streaming command string at 0x1f32a2 (overwriting unused [fangjj] debug string)
cmd_str = b"/mnt/extsd/start_streaming.sh &\x00"
assert len(cmd_str) <= 38, "Command string too long"
data[0x1f32a2 : 0x1f32a2 + len(cmd_str)] = cmd_str

# 5. Unblock keys at startup (NOP out bne.w 57522 at 0x472ea)
data[0x472ea : 0x472ea + 4] = bytes.fromhex("00bf00bf")

with open(OUT_PATH, "wb") as f:
    f.write(data)

final_md5 = hashlib.md5(data).hexdigest()
print(f"Wrote {OUT_PATH}: MD5 = {final_md5}")

# List diffs
diffs = []
i = 0
with open(V8_PATH, "rb") as f:
    v8 = f.read()
while i < len(v8):
    if v8[i] != data[i]:
        start = i
        while i < len(v8) and v8[i] != data[i]:
            i += 1
        diffs.append((start, i - start, v8[start:i], data[start:i]))
    else:
        i += 1

print(f"\nTotal diff chunks between v8 and 4tiles: {len(diffs)}")
for off, sz, old_b, new_b in diffs:
    print(f"Offset {hex(off)} ({off}), len {sz}: {old_b.hex()} -> {new_b.hex()}")

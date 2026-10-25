import hashlib, subprocess

V8_PATH = r"d:\v316cm\sdvcam_v8"
OUT_PATH = r"d:\v316cm\sdvcam_4tiles_v2"

with open(V8_PATH, "rb") as f:
    data = bytearray(f.read())

print(f"Loaded sdvcam_v8: {len(data)} bytes, MD5: {hashlib.md5(data).hexdigest()}")

# 1. Front button inside FunctionSelectWindow advances tile
# Offset 0x59852: change 0x15 -> 0x0b
print(f"Byte at 0x59852 before: {hex(data[0x59852])}")
data[0x59852] = 0x0b

# 2. FunctionChangeProc 4-Tile Action Dispatcher at 0x4afe0 (76 bytes)
with open(r"d:\v316cm\asm_patch.elf", "rb") as f:
    p_elf = f.read()
p_pos = p_elf.find(b"\x30\xb5\x04\x46\x15\x46")
assert p_pos != -1, "Dispatcher pattern not found in asm_patch.elf"
disp_bytes = p_elf[p_pos : p_pos + 76]
data[0x4afe0 : 0x4afe0 + len(disp_bytes)] = disp_bytes

# 3. Streaming command string at 0x1f32a2 (overwriting unused [fangjj] debug string)
cmd_str = b"/mnt/extsd/start_streaming.sh &\x00"
assert len(cmd_str) <= 38, "Command string too long"
data[0x1f32a2 : 0x1f32a2 + len(cmd_str)] = cmd_str

# 4. Front button in PreviewWindow (short press) jumps cleanly to KeyFunctionProc
# File offset 0x4ba46 (vaddr 0x5ba46): replace b.w 0x5aa08 with b.w 0x5b030 (ff f7 f3 ba)
print(f"Bytes at 0x4ba46 before: {data[0x4ba46:0x4ba46+4].hex()}")
data[0x4ba46 : 0x4ba46 + 4] = bytes.fromhex("fff7f3ba")

# 5. Boot hook in PreviewPresenter::OnWindowLoaded
# File offset 0x5c0ee (vaddr 0x6c0ee): 16 bytes
# add sp, #12; ldmia.w sp!, {r4, r5, lr}; b.w 0x5b030; nop; nop; nop
boot_hook = bytes.fromhex("03b0bde83040eef79cbf00bf00bf00bf")
assert len(boot_hook) == 16
print(f"Bytes at 0x5c0ee before: {data[0x5c0ee:0x5c0ee+16].hex()}")
data[0x5c0ee : 0x5c0ee + 16] = boot_hook

with open(OUT_PATH, "wb") as f:
    f.write(data)

final_md5 = hashlib.md5(data).hexdigest()
print(f"\nWrote {OUT_PATH}: MD5 = {final_md5}")

# List diffs against v8
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

print(f"\nTotal diff chunks between v8 and 4tiles_v2: {len(diffs)}")
for off, sz, old_b, new_b in diffs:
    print(f"Offset {hex(off)} ({off}), len {sz}: {old_b.hex()} -> {new_b.hex()}")

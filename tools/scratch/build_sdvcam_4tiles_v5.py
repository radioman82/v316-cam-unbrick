"""
Build sdvcam_4tiles_v5 from the clean v8 image.

SAFE variant: no boot hook (OnWindowLoaded fires before FunctionSelectWindow
exists -> [self+0x114] is NULL -> SIGABRT at PC 0x6c0f2).

Contains only:
  B) front button inside FunctionSelectWindow cycles the tile
  C) 4-tile action dispatcher
  D) front button in preview re-opens the menu
  + streaming command string
"""
import hashlib, os

HERE = os.path.dirname(os.path.abspath(__file__))
V8_PATH = os.path.join(HERE, "sdvcam_v8")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_v5")

with open(V8_PATH, "rb") as f:
    data = bytearray(f.read())
print(f"v8: {len(data)} bytes, MD5 {hashlib.md5(data).hexdigest()}")

# B) front button inside FunctionSelectWindow cycles the tile
data[0x59852] = 0x0b

# C) 4-tile action dispatcher (76 bytes)
with open(os.path.join(HERE, "asm_patch.elf"), "rb") as f:
    p_elf = f.read()
p_pos = p_elf.find(b"\x30\xb5\x04\x46\x15\x46")
assert p_pos != -1
data[0x4afe0:0x4afe0 + 76] = p_elf[p_pos:p_pos + 76]

# streaming command string
cmd_str = b"/mnt/extsd/start_streaming.sh &\x00"
data[0x1f32a2:0x1f32a2 + len(cmd_str)] = cmd_str

# D) front button in preview re-opens the menu
data[0x4ba46:0x4ba46 + 4] = bytes.fromhex("fff7f3ba")

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"Wrote {OUT_PATH}\nMD5 = {hashlib.md5(data).hexdigest()}")

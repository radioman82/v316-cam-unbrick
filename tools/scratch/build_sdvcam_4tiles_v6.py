"""
Build sdvcam_4tiles_v6 from the clean v8 image.

v6 = v5, but the front button in the preview window now calls
FunctionSelectWindow::Show() directly through a code cave instead of jumping
into KeyFunctionProc (which aborts in its cold-start guards).

  B) 0x59852        0x15 -> 0x0b      (menu key cycles the tile)
  C) 0x4afe0        76-byte action dispatcher
  D) 0x4ba46        b.w 0x1f5130      (code cave -> direct Show())
    0x1f5130        cave stub (+ /tmp/KEYHIT marker)
"""
import hashlib, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
V8_PATH = os.path.join(HERE, "sdvcam_v8")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_v6")
ASM = os.path.join(HERE, "show_stub_v6.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout

obj = os.path.join(HERE, "show_stub_v6.o")
elf = os.path.join(HERE, "show_stub_v6.elf")
bin_ = os.path.join(HERE, "show_stub_v6.bin")
sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{bin_}"')

with open(bin_, "rb") as f:
    stubbin = f.read()

jump = stubbin[0x5ba46:0x5ba46 + 4]
cave = stubbin[0x1f5130:0x1f5130 + 64]
print("jump @0x5ba46:", jump.hex())
print("cave @0x1f5130:", cave[:48].hex())

with open(V8_PATH, "rb") as f:
    data = bytearray(f.read())
v8 = bytes(data)
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

# D) front button -> code cave -> direct Show()
# NOTE: cave lives at vaddr 0x1f5130 == file offset 0x1e5130
CAVE_FILE_OFF = 0x1e5130
data[0x4ba46:0x4ba46 + 4] = jump
data[CAVE_FILE_OFF:CAVE_FILE_OFF + len(cave)] = cave

assert len(data) == len(v8), f"length changed: {len(data)} != {len(v8)}"

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"Wrote {OUT_PATH}\nMD5 = {hashlib.md5(data).hexdigest()}")

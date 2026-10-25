"""
Build sdvcam_4tiles_v3 from the clean v8 image.

Fixes over v2:
  A) Boot hook at 0x5c0ee passed the WRONG r0.
     v2 replaced the vtable call at 0x6c0ee but left r0 = [self+0x90]
     (a child object), so KeyFunctionProc at 0x5b030 did
     `mov r4, r0; ldr.w r0,[r4,#0x114]` on the wrong object -> crash / no menu.
     v3 loads r0 = r4 (self) before the tail branch.
  A2) The `cbz r0, 0x6c0fe` guard at 0x5c0ec is NOPed so the hook is
     unconditional (r0 no longer matters).
"""
import hashlib, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
V8_PATH = os.path.join(HERE, "sdvcam_v8")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_v3")
ASM = os.path.join(HERE, "boot_hook_v3.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout

# ---- 1. assemble the boot hook -------------------------------------------
obj = os.path.join(HERE, "boot_hook_v3.o")
elf = os.path.join(HERE, "boot_hook_v3.elf")
bin_ = os.path.join(HERE, "boot_hook_v3.bin")
sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{bin_}"')

with open(bin_, "rb") as f:
    raw = f.read()
hook = raw[0x6c0ee:0x6c0ee + 16]
assert len(hook) == 16, f"hook length {len(hook)}"
print("boot hook bytes:", hook.hex())

# ---- 2. load v8 ----------------------------------------------------------
with open(V8_PATH, "rb") as f:
    data = bytearray(f.read())
v8 = bytes(data)
print(f"v8: {len(data)} bytes, MD5 {hashlib.md5(v8).hexdigest()}")

# ---- 3. patches ----------------------------------------------------------
# B) front button inside FunctionSelectWindow cycles the tile
print(f"0x59852: {data[0x59852]:#04x} -> 0x0b")
data[0x59852] = 0x0b

# C) 4-tile action dispatcher (76 bytes) replaces FunctionChangeProc body
with open(os.path.join(HERE, "asm_patch.elf"), "rb") as f:
    p_elf = f.read()
p_pos = p_elf.find(b"\x30\xb5\x04\x46\x15\x46")
assert p_pos != -1, "dispatcher pattern not found"
disp = p_elf[p_pos:p_pos + 76]
assert len(disp) == 76
data[0x4afe0:0x4afe0 + 76] = disp

# streaming command string
cmd_str = b"/mnt/extsd/start_streaming.sh &\x00"
data[0x1f32a2:0x1f32a2 + len(cmd_str)] = cmd_str

# D) front button in preview re-opens the menu
print(f"0x4ba46: {bytes(data[0x4ba46:0x4ba46+4]).hex()} -> fff7f3ba")
data[0x4ba46:0x4ba46 + 4] = bytes.fromhex("fff7f3ba")

# A2) make the boot hook unconditional
# NOP is halfword 0xBF00 -> little-endian bytes 00 BF
print(f"0x5c0ec: {bytes(data[0x5c0ec:0x5c0ec+2]).hex()} -> 00bf (nop)")
data[0x5c0ec:0x5c0ec + 2] = bytes.fromhex("00bf")

# A) fixed boot hook
print(f"0x5c0ee: {bytes(data[0x5c0ee:0x5c0ee+16]).hex()} -> {hook.hex()}")
data[0x5c0ee:0x5c0ee + 16] = hook

# ---- 4. write ------------------------------------------------------------
with open(OUT_PATH, "wb") as f:
    f.write(data)
final_md5 = hashlib.md5(data).hexdigest()
print(f"\nWrote {OUT_PATH}\nMD5 = {final_md5}")

# ---- 5. diff -------------------------------------------------------------
diffs = []
i = 0
while i < len(v8):
    if v8[i] != data[i]:
        s = i
        while i < len(v8) and v8[i] != data[i]:
            i += 1
        diffs.append((s, i - s))
    else:
        i += 1
print(f"\n{len(diffs)} diff chunk(s) vs v8:")
for off, sz in diffs:
    print(f"  0x{off:06x}  {sz:3d} bytes")

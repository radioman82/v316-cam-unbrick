"""
Build sdvcam_4tiles_v4 from the clean v8 image.

Change vs v3:
  A) The boot hook now calls FunctionSelectWindow::Show() DIRECTLY via
     vtable+0x6c instead of jumping into KeyFunctionProc (0x5b030).
     KeyFunctionProc has cold-start guards ([self+0x160], [self+0x17c],
     [self+0x168]) that abort before the Show() at 0x5b0b4, which is why
     the 4 tiles never appeared on a fresh boot.
"""
import hashlib, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
V8_PATH = os.path.join(HERE, "sdvcam_v8")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_v4")
ASM = os.path.join(HERE, "boot_hook_v4.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout

obj = os.path.join(HERE, "boot_hook_v4.o")
elf = os.path.join(HERE, "boot_hook_v4.elf")
bin_ = os.path.join(HERE, "boot_hook_v4.bin")
sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{bin_}"')

with open(bin_, "rb") as f:
    raw = f.read()
hook = raw[0x6c0ee:0x6c0ee + 16]
assert len(hook) == 16
print("boot hook bytes:", hook.hex(), f"({len(hook)} bytes)")

with open(V8_PATH, "rb") as f:
    data = bytearray(f.read())
v8 = bytes(data)
print(f"v8: {len(data)} bytes, MD5 {hashlib.md5(v8).hexdigest()}")

# B) front button inside FunctionSelectWindow cycles the tile
data[0x59852] = 0x0b

# C) 4-tile action dispatcher (76 bytes)
with open(os.path.join(HERE, "asm_patch.elf"), "rb") as f:
    p_elf = f.read()
p_pos = p_elf.find(b"\x30\xb5\x04\x46\x15\x46")
assert p_pos != -1
disp = p_elf[p_pos:p_pos + 76]
data[0x4afe0:0x4afe0 + 76] = disp

# streaming command string
cmd_str = b"/mnt/extsd/start_streaming.sh &\x00"
data[0x1f32a2:0x1f32a2 + len(cmd_str)] = cmd_str

# D) front button in preview re-opens the menu
data[0x4ba46:0x4ba46 + 4] = bytes.fromhex("fff7f3ba")

# A) direct Show() hook
# NOP the `cbz r0, 0x6c0fe` guard at 0x5c0ec first so the hook is unconditional
data[0x5c0ec:0x5c0ec + 2] = bytes.fromhex("00bf")
data[0x5c0ee:0x5c0ee + 16] = hook

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"\nWrote {OUT_PATH}\nMD5 = {hashlib.md5(data).hexdigest()}")

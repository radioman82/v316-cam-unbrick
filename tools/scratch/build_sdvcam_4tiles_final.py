"""
Build sdvcam_4tiles_final from the clean v8 image.

Working 4-tile build:
  B) 0x59852   0x15 -> 0x0b    menu key cycles the tile
  C) 0x4afe0   76-byte action dispatcher (Foto / Video / Stream / Setup)
  D) 0x4ba46   b.w 0x1f5130    front button opens the menu (direct Show())
  + streaming command string

No boot hook: OnWindowLoaded runs before FunctionSelectWindow exists
([self+0x114] == NULL -> SIGABRT at 0x6c0f2), and the window-init epilogue at
0x48608 is also reached with r4 == NULL (SIGSEGV at 0x1f5146).
"""
import hashlib, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
V8_PATH = os.path.join(HERE, "sdvcam_v8")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_final")
ASM = os.path.join(HERE, "show_stub_final.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout

obj = os.path.join(HERE, "show_stub_final.o")
elf = os.path.join(HERE, "show_stub_final.elf")
bin_ = os.path.join(HERE, "show_stub_final.bin")
sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{bin_}"')

with open(bin_, "rb") as f:
    stubbin = f.read()

with open(V8_PATH, "rb") as f:
    data = bytearray(f.read())
v8 = bytes(data)
print(f"v8: {len(data)} bytes, MD5 {hashlib.md5(v8).hexdigest()}")

def apply(vaddr, ln, name):
    off = vaddr - 0x10000
    data[off:off + ln] = stubbin[vaddr:vaddr + ln]
    print(f"  {name}: vaddr 0x{vaddr:05x} -> file 0x{off:05x}  {stubbin[vaddr:vaddr+ln].hex()}")

print("patches:")
data[0x59852] = 0x0b
print("  B  menu key cycles tile: file 0x59852 = 0x0b")

with open(os.path.join(HERE, "asm_patch.elf"), "rb") as f:
    p_elf = f.read()
p_pos = p_elf.find(b"\x30\xb5\x04\x46\x15\x46")
assert p_pos != -1
data[0x4afe0:0x4afe0 + 76] = p_elf[p_pos:p_pos + 76]
print("  C  action dispatcher: file 0x4afe0 (76 bytes)")

cmd_str = b"/mnt/extsd/start_streaming.sh &\x00"
data[0x1f32a2:0x1f32a2 + len(cmd_str)] = cmd_str
print(f"  +  streaming string: file 0x1f32a2 ({len(cmd_str)} bytes)")

apply(0x5ba46, 4, "D  front button -> cave")
apply(0x1f5130, 10, "cave Show() stub")

assert len(data) == len(v8), f"length changed: {len(data)} != {len(v8)}"

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"Wrote {OUT_PATH}\nMD5 = {hashlib.md5(data).hexdigest()}")

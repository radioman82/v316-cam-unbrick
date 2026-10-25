"""
Build sdvcam_4tiles_v7 from the clean v8 image.

v7 = v6 without the key-path debug marker, plus an autostart hook.

  B) 0x59852        0x15 -> 0x0b      menu key cycles the tile
  C) 0x4afe0        76-byte action dispatcher
  D) 0x4ba46        b.w 0x1f5130      front button -> Show()
    0x48608         b.w 0x1f5140      end of window init -> Show()  (autostart)
"""
import hashlib, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
V8_PATH = os.path.join(HERE, "sdvcam_v8")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_v7")
ASM = os.path.join(HERE, "show_stub_v7.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout

obj = os.path.join(HERE, "show_stub_v7.o")
elf = os.path.join(HERE, "show_stub_v7.elf")
bin_ = os.path.join(HERE, "show_stub_v7.bin")
sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{bin_}"')

with open(bin_, "rb") as f:
    stubbin = f.read()

def v2f(vaddr):
    """vaddr -> file offset inside the sdvcam image"""
    return vaddr - 0x10000

with open(V8_PATH, "rb") as f:
    data = bytearray(f.read())
v8 = bytes(data)
print(f"v8: {len(data)} bytes, MD5 {hashlib.md5(v8).hexdigest()}")

# --- patches -------------------------------------------------------------
data[0x59852] = 0x0b                                    # B

with open(os.path.join(HERE, "asm_patch.elf"), "rb") as f:   # C
    p_elf = f.read()
p_pos = p_elf.find(b"\x30\xb5\x04\x46\x15\x46")
assert p_pos != -1
data[0x4afe0:0x4afe0 + 76] = p_elf[p_pos:p_pos + 76]

cmd_str = b"/mnt/extsd/start_streaming.sh &\x00"          # streaming string
data[0x1f32a2:0x1f32a2 + len(cmd_str)] = cmd_str

# --- stubs: assembled image uses vaddr == file offset; firmware uses vaddr-0x10000 ---
def apply(vaddr, ln, name):
    off = vaddr - 0x10000
    data[off:off + ln] = stubbin[vaddr:vaddr + ln]
    print(f"  {name}: vaddr 0x{vaddr:06x} -> file 0x{off:06x} ({ln} bytes) {stubbin[vaddr:vaddr+ln].hex()}")

print("patched regions:")
apply(0x5ba46, 4, "D  front button -> cave")            # D
apply(0x48608, 4, "A  boot hook -> cave")               # A
apply(0x1f5130, 12, "cave key stub")
apply(0x1f5140, len(stubbin) - 0x1f5140, "cave boot stub")

assert len(data) == len(v8), f"length changed: {len(data)} != {len(v8)}"

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"Wrote {OUT_PATH}\nMD5 = {hashlib.md5(data).hexdigest()}")

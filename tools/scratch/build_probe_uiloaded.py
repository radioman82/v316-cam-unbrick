"""
Probe build: test if [r4+0x114] (func_win) is set when OnUILoaded runs.
Hooks OnUILoaded epilogue at 0x6aec0, writes /tmp/UILOADED_OK or /tmp/UILOADED_NULL.
No Show() call — safe probe only.

Based on sdvcam_4tiles_final + probe hook.
"""
import hashlib, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
V8_PATH = os.path.join(HERE, "sdvcam_v8")
FINAL_PATH = os.path.join(HERE, "sdvcam_4tiles_final")
OUT_PATH = os.path.join(HERE, "sdvcam_4tiles_probe")
ASM = os.path.join(HERE, "probe_uiloaded.s")
TOOL = r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin"

def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {cmd}\n{r.stdout}\n{r.stderr}")
    return r.stdout

obj = os.path.join(HERE, "probe_uiloaded.o")
elf = os.path.join(HERE, "probe_uiloaded.elf")
bin_ = os.path.join(HERE, "probe_uiloaded.bin")
sh(f'"{TOOL}\\arm-none-eabi-as.exe" -mthumb -o "{obj}" "{ASM}"')
sh(f'"{TOOL}\\arm-none-eabi-ld.exe" -Ttext=0x0 -o "{elf}" "{obj}"')
sh(f'"{TOOL}\\arm-none-eabi-objcopy.exe" -O binary "{elf}" "{bin_}"')

with open(bin_, "rb") as f:
    stubbin = f.read()

# Start from the already-working final build
with open(FINAL_PATH, "rb") as f:
    data = bytearray(f.read())
base = bytes(data)
print(f"final: {len(data)} bytes, MD5 {hashlib.md5(base).hexdigest()}")
assert hashlib.md5(base).hexdigest() == "5ce4e6c6f7125394b099dae940f124ed", "final MD5 mismatch!"

def apply(vaddr, ln, name):
    off = vaddr - 0x10000
    data[off:off + ln] = stubbin[vaddr:vaddr + ln]
    print(f"  {name}: vaddr 0x{vaddr:06x} -> file 0x{off:06x} ({ln} bytes) {stubbin[vaddr:vaddr+ln].hex()}")

print("NEW patches on top of final:")
apply(0x6aec0, 4, "E  OnUILoaded epilogue -> probe cave")
apply(0x1f5150, len(stubbin) - 0x1f5150, "probe cave")

assert len(data) == len(base), f"length changed: {len(data)} != {len(base)}"

with open(OUT_PATH, "wb") as f:
    f.write(data)
print(f"Wrote {OUT_PATH}\nMD5 = {hashlib.md5(data).hexdigest()}")

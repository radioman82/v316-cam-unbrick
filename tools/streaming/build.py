"""Build a self-contained ARMv7 Linux CGI using Zig 0.14.1 (no camera libraries)."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parents[1] / "firmware" / "streaming" / "v316cm-mjpeg"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zig", default=shutil.which("zig"), help="Path to zig executable")
    args = parser.parse_args()
    if not args.zig:
        parser.error("Install Zig 0.14.1 and supply --zig PATH (https://ziglang.org/download/)")
    header = HERE / "vendor" / "stb_image_write.h"
    expected = "cbd5f0ad7a9cf4468affb36354a1d2338034f2c12473cf1a8e32053cb6914a05"
    if hashlib.sha256(header.read_bytes()).hexdigest() != expected:
        raise SystemExit("Vendored JPEG header checksum mismatch")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        args.zig, "cc", "-target", "arm-linux-musleabihf", "-mcpu=cortex_a7",
        "-O2", "-static", "-s", "-fno-strict-aliasing", "-ffunction-sections",
        "-fdata-sections", "-Wl,--gc-sections", "-Wall", "-Wextra",
        "-Wno-unused-function", str(HERE / "v316cm_mjpeg.c"), "-lm", "-o", str(OUTPUT),
    ], check=True)
    print(f"{OUTPUT}: {OUTPUT.stat().st_size} bytes")
    print("SHA256:", hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
    control = OUTPUT.with_name('v316cm-control')
    subprocess.run([
        args.zig, 'cc', '-target', 'arm-linux-musleabihf', '-mcpu=cortex_a7',
        '-O2', '-static', '-s', '-Wall', '-Wextra',
        str(HERE / 'v316cm_control.c'), '-o', str(control),
    ], check=True)
    print(f'{control}: {control.stat().st_size} bytes')
    direct = OUTPUT.with_name('libv316cm-direct.so')
    subprocess.run([
        args.zig, 'cc', '-target', 'arm-linux-gnueabi.2.21', '-mcpu=cortex_a7',
        '-O2', '-shared', '-fPIC', '-s', '-Wall', '-Wextra',
        '-ffunction-sections', '-fdata-sections', '-Wl,--gc-sections',
        '-Wl,--version-script=' + str(HERE / 'direct.exports'),
        str(HERE / 'v316cm_direct.c'), '-pthread', '-ldl', '-o', str(direct),
    ], check=True)
    print(f'{direct}: {direct.stat().st_size} bytes')


if __name__ == "__main__":
    main()

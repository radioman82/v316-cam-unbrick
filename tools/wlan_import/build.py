"""Build the static ARM WLAN importer and a native data-parser test harness."""
import argparse
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zig', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--host-test', action='store_true')
    args = p.parse_args()
    folder = args.output.parent
    folder.mkdir(parents=True, exist_ok=True)
    target = 'x86_64-windows-gnu' if args.host_test else 'arm-linux-musleabihf'
    cpu = [] if args.host_test else ['-mcpu=cortex_a7']
    library = folder / ('wlan-crypto.lib' if args.host_test else 'wlan-crypto.a')
    subprocess.run([args.zig, 'build-lib', str(HERE/'crypto.zig'), '-target', target,
                    *cpu, '-O', 'ReleaseFast', '-static', '-femit-bin='+str(library)], check=True)
    if not args.host_test:
        f = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 15)
        rows = []
        for code in range(32, 127):
            im = Image.new('1', (9, 18))
            ImageDraw.Draw(im).text((0, -1), chr(code), font=f, fill=1)
            rows.append('{'+','.join(str(sum(im.getpixel((x,y)) << x for x in range(9))) for y in range(18))+'}')
        (folder/'update_font.h').write_text('static const unsigned short font[95][18]={\n'+',\n'.join(rows)+'\n};\n')
    source = HERE / ('test_harness.c' if args.host_test else 'import.c')
    subprocess.run([args.zig, 'cc', '-target', target, *cpu, '-O2', '-static', '-s',
                    '-Wall', '-Wextra', '-Werror', '-Wno-unused-function', '-Wno-misleading-indentation',
                    '-I', str(folder), str(source), str(library), '-o', str(args.output)], check=True)
    print(args.output, args.output.stat().st_size)


if __name__ == '__main__':
    main()

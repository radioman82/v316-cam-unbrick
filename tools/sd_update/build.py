"""Build the static ARM RAM updater and its embedded display font."""
import argparse
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zig', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 15)
    rows = []
    for code in range(32, 127):
        im = Image.new('1', (9, 18))
        ImageDraw.Draw(im).text((0, -1), chr(code), font=font, fill=1)
        rows.append('{' + ','.join(str(sum(im.getpixel((x, y)) << x for x in range(9))) for y in range(18)) + '}')
    header = args.output.parent / 'update_font.h'
    header.write_text('static const unsigned short font[95][18]={\n' + ',\n'.join(rows) + '\n};\n')
    cmd = [args.zig, 'cc', '-target', 'arm-linux-musleabihf', '-mcpu=cortex_a7',
           '-O2', '-static', '-s', '-Wall', '-Wextra', '-Werror', '-I', str(header.parent),
           str(HERE / 'updater.c'), '-o', str(args.output)]
    subprocess.run(cmd, check=True)
    print(args.output, args.output.stat().st_size)


if __name__ == '__main__':
    main()

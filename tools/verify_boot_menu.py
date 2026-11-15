"""Verify the installed boot-menu fix and its rendered four-quadrant image."""
import argparse
import hashlib
import io
import json
from pathlib import Path

from dissect.squashfs import SquashFS
from PIL import Image

from camera_uart import CameraUART


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    p.add_argument('--label', default='after-install')
    args = p.parse_args()
    image = (args.folder/'V316CM_BOOT_MENU_PRIVATE_16MiB.bin').read_bytes()
    manifest = json.loads((args.folder/'manifest.json').read_text())
    assert hashlib.sha256(image).hexdigest() == manifest['sha256']
    fs = SquashFS(io.BytesIO(image[0x400000:0xe80000]))
    audio = fs.get('/usr/share/minigui/res/audio/startup.wav').open().read()
    c = CameraUART()
    try:
        checks = c.run('md5sum /dev/mtdblock2 /usr/share/minigui/res/audio/startup.wav /mnt/extsd/firmware-update.done', 30).splitlines()
        actual = [x.split()[0] for x in checks]
        expected = [manifest['rootfs_md5'], hashlib.md5(audio).hexdigest(), hashlib.md5((args.folder/'firmware-update.bin').read_bytes()).hexdigest()]
        assert actual == expected, (actual, expected)
        log = c.run('cat /tmp/startup-menu.log', 10)
        assert 'BOOT_MENU ready pid=' in log and '"ok":true' in log
        status = json.loads(c.run('/opt/cam/bin/ct9000-control status', 10))
        assert status['ok'] and status['preview'] and status['tiles'] and not status['recording']
        keys = c.run('grep -c MSG_KEYDOWN /tmp/sdvcam.log; true', 10)
        # Older installed control builds implement menu via two synthetic key
        # presses. These appear in the same log as physical input.
        key_events = int(keys.strip())
        c.run('sleep 10; dd if=/dev/fb0 of=/tmp/codex-boot-fb.raw bs=307200 count=1 2>/dev/null', 20)
        data = c.read('/tmp/codex-boot-fb.raw', 30)
        im = Image.frombytes('RGBA', (320,240), data, 'raw', 'BGRA')
        colored = []
        for box in ((0,0,160,120),(160,0,320,120),(0,120,160,240),(160,120,320,240)):
            colored.append(sum(1 for r,g,b,a in im.crop(box).getdata() if max(r,g,b)-min(r,g,b)>100 and max(r,g,b)>140))
        assert min(colored) > 150, ('Missing tile artwork', colored)
        again = json.loads(c.run('/opt/cam/bin/ct9000-control status', 10))
        assert again['pid'] == status['pid'] and again['tiles']
        im.save(args.folder/f'boot-screen-{args.label}.png')
        report = {'status': 'boot helper and rendered menu verified', 'rootfs_md5': actual[0], 'startup_md5': actual[1], 'package_md5': actual[2], 'window_state': again, 'colored_pixels_per_quadrant': colored, 'startup_log': log, 'key_events_in_log': key_events, 'note': 'Installed menu control may generate two synthetic keys; log cannot distinguish these from physical keys.'}
        (args.folder/f'verification-{args.label}.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2), flush=True)
    finally:
        c.close()


if __name__ == '__main__':
    main()

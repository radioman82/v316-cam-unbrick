"""Verify the installed GUI fix without delayed helpers or synthetic keys."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from camera_uart import CameraUART


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    args = p.parse_args()
    manifest = json.loads((args.folder/'manifest.json').read_text())
    c = CameraUART()
    try:
        checks = c.run('md5sum /dev/mtdblock2 /usr/bin/sdvcam /usr/share/minigui/res/audio/startup.wav /mnt/extsd/firmware-update.done',30).splitlines()
        actual = [line.split()[0] for line in checks]
        expected = [manifest['rootfs_md5'],manifest['app_md5'],'d7fd94bb2a8b9c392a37d66e6c8515e9',hashlib.md5((args.folder/'firmware-update.bin').read_bytes()).hexdigest()]
        assert actual == expected,(actual,expected)
        c.run('test ! -e /opt/cam/startup_menu.sh && cmp /etc/init.d/S01app /squashfs/etc/init.d/S01app')
        keys = c.run('grep -c MSG_KEYDOWN /tmp/sdvcam.log; true').strip()
        assert keys == '0',keys
        state = json.loads(c.run('/opt/cam/bin/ct9000-control status'))
        assert state['tiles'] and state['preview'] and not state['recording']
        c.run('sleep 8; dd if=/dev/fb0 of=/tmp/gui-verified-frame.raw bs=307200 count=1 2>/dev/null',20)
        raw = c.read('/tmp/gui-verified-frame.raw',30)
        im = Image.frombytes('RGBA',(320,240),raw,'raw','BGRA')
        colored = sum(1 for r,g,b,a in im.getdata() if max(r,g,b)-min(r,g,b)>100 and max(r,g,b)>140)
        assert colored > 3000,colored
        im.save(args.folder/'verified-boot-screen.png')
        again = json.loads(c.run('/opt/cam/bin/ct9000-control status'))
        assert again['pid'] == state['pid'] and again['tiles']
        report = {'status':'installed and verified after boot without delayed helper or key events','rootfs_md5':actual[0],'app_md5':actual[1],'startup_md5':actual[2],'package_md5':actual[3],'key_events':0,'colored_pixels':colored,'window_state':again}
        (args.folder/'verification.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2),flush=True)
    finally:
        c.close()


if __name__ == '__main__':
    main()

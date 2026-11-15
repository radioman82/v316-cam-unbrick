"""Test a single replacement camera app via reboot-volatile bind mounts."""
import argparse
import base64
import ftplib
import hashlib
import json
from pathlib import Path
import time

from PIL import Image
from camera_uart import CameraUART


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary', type=Path)
    p.add_argument('host')
    p.add_argument('output', type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    c = CameraUART()
    server = None
    stopped = False
    bound_app = False
    bound_helper = False
    try:
        status = json.loads(c.run('/opt/cam/bin/ct9000-control status'))
        assert not status['recording']
        c.run('mkdir -p /mnt/extsd/gui-startup-test-20261102')
        c.run('if [ ! -e /mnt/extsd/gui-startup-test-20261102/previous-sdvcam ]; then cp /usr/bin/sdvcam /mnt/extsd/gui-startup-test-20261102/previous-sdvcam; fi; sync')
        server = c.run('/opt/cam/bin/busybox tcpsvd -E 0.0.0.0 18021 /opt/cam/bin/busybox ftpd -w -A /mnt/extsd/gui-startup-test-20261102 >/tmp/gui-test-ftp.log 2>&1 </dev/null & echo $!').splitlines()[-1]
        assert server.isdigit()
        with ftplib.FTP() as ftp:
            ftp.connect(args.host, 18021, timeout=30)
            ftp.login()
            with args.binary.open('rb') as source:
                ftp.storbinary('STOR sdvcam', source)
        expected = hashlib.md5(args.binary.read_bytes()).hexdigest()
        assert c.run('md5sum /mnt/extsd/gui-startup-test-20261102/sdvcam').split()[0] == expected
        c.run('chmod 755 /mnt/extsd/gui-startup-test-20261102/sdvcam')
        encoded = base64.b64encode(b'#!/bin/sh\nexit 0\n').decode()
        c.run(f'printf %s {encoded} | /opt/cam/bin/busybox base64 -d > /tmp/gui-test-no-delayed-menu')
        c.run('mount --bind /tmp/gui-test-no-delayed-menu /opt/cam/startup_menu.sh')
        bound_helper = True
        c.run('/etc/init.d/S01app stop; sleep 2; /opt/cam/bin/busybox killall -9 sdvcam 2>/dev/null; sleep 1; true')
        # Check separately because the vendor shell does not have pipefail.
        assert c.run('/opt/cam/bin/busybox pidof sdvcam; true').strip() == ''
        stopped = True
        c.run('mount --bind /mnt/extsd/gui-startup-test-20261102/sdvcam /usr/bin/sdvcam')
        bound_app = True
        c.run('/etc/init.d/S01app start')
        c.run('sleep 12', 20)
        status = json.loads(c.run('/opt/cam/bin/ct9000-control status'))
        print('STATUS', json.dumps(status), flush=True)
        assert status['ok'] and status['tiles'] and status['preview']
        assert c.run('grep -c MSG_KEYDOWN /tmp/sdvcam.log; true').strip() == '0'
        c.run('sleep 8; dd if=/dev/fb0 of=/tmp/gui-test-frame.raw bs=307200 count=1 2>/dev/null', 20)
        data = c.read('/tmp/gui-test-frame.raw', 30)
        im = Image.frombytes('RGBA', (320,240), data, 'raw', 'BGRA')
        im.save(args.output/'screen.png')
        count = sum(1 for r,g,b,a in im.getdata() if max(r,g,b)-min(r,g,b)>100 and max(r,g,b)>140)
        print('COLORED_PIXELS', count, flush=True)
        assert count > 3000
        again = json.loads(c.run('/opt/cam/bin/ct9000-control status'))
        assert again['pid'] == status['pid'] and again['tiles']
        (args.output/'verification.json').write_text(json.dumps({'status': 'RAM-bind test passed without delayed helper or key events', 'app_md5': expected, 'window_state': again, 'colored_pixels': count}, indent=2))
        print('RAM_TEST_PASSED; reboot returns to installed image', flush=True)
    except BaseException:
        if stopped:
            c.run('/etc/init.d/S01app stop; sleep 1; /opt/cam/bin/busybox killall -9 sdvcam 2>/dev/null; sleep 1; true', 15)
            assert c.run('/opt/cam/bin/busybox pidof sdvcam; true').strip() == ''
        if bound_app:
            c.run('umount /usr/bin/sdvcam')
        if bound_helper:
            c.run('umount /opt/cam/startup_menu.sh')
        if stopped:
            c.run('/etc/init.d/S01app start')
        raise
    finally:
        if server:
            c.run(f'kill {server} 2>/dev/null; true')
        c.close()


if __name__ == '__main__':
    main()

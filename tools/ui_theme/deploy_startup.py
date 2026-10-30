"""Install an app-only update on the already verified v23 camera app.

Only the changed app regions are transferred. The active app and SD copies are
backed up before replacement; theme artwork and flash partitions are untouched.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'streaming'))
from deploy import Camera


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'firmware/ui_theme'
BASE_MD5 = '211d51fe21a397c73ea6a3ce8f6a0e13'
START = 'FB_SYNC=1 SCREEN_INFO=240x376-32bpp LD_HWCAP_MASK=0x00000000 /usr/bin/sdvcam >/tmp/sdvcam.log 2>&1 </dev/null &'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-md5', default=BASE_MD5,
                        help='Expected current app checksum (defaults to pre-startup v23)')
    args = parser.parse_args()
    data = (OUT / 'sdvcam_menu_v23').read_bytes()
    manifest = json.loads((OUT / 'manifest.json').read_text())
    target_md5 = hashlib.md5(data).hexdigest()
    assert target_md5 == manifest['md5']
    c = Camera('http://192.168.178.199:8080')
    installed = c.run('md5sum /usr/bin/sdvcam /mnt/extsd/sdvcam /mnt/extsd/.sdvcam_patched')
    hashes = [line.split()[0] for line in installed.splitlines()]
    if hashes == [target_md5] * 3:
        print('Startup menu already installed:', target_md5)
        return
    if hashes != [args.base_md5] * 3:
        raise RuntimeError(f'Unexpected installed app hashes: {hashes}')
    if c.run('cat /mnt/extsd/ui_theme/current/enabled') != args.base_md5:
        raise RuntimeError('Theme enable hash does not match the active app')
    marker_state = c.run('if grep -q /tmp/v316cm-stream-mode /mnt/extsd/network_mode.sh && grep -q /tmp/v316cm-stream-mode /mnt/extsd/start_streaming.sh && grep -q /tmp/v316cm-stream-ready /mnt/extsd/stop_streaming.sh; then echo OK; else echo OLD; fi')
    if marker_state != 'OK':
        raise RuntimeError('SD stream scripts use old markers; install the complete UI package first')
    pid = c.run('pidof sdvcam')
    fds = c.run(f'for f in /proc/{pid}/fd/*; do readlink "$f"; done; true')
    if any('/DCIM/' in path and path.endswith(('.mp4', '.sec')) for path in fds.splitlines()):
        raise RuntimeError('Stop recording or playback before updating')

    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    base = f'/mnt/extsd/ui_theme/startup-{stamp}'
    backup, stage = base + '-backup', base + '-stage'
    c.run(f'mkdir -p {backup} {stage}; cp /usr/bin/sdvcam {backup}/sdvcam; cp /mnt/extsd/sdvcam {backup}/sdvcam_sd; cp /mnt/extsd/.sdvcam_patched {backup}/boot_binary; cp /mnt/extsd/ui_theme/current/enabled {backup}/enabled; cp /usr/bin/sdvcam {stage}/sdvcam')
    print('Backup:', backup, flush=True)
    for offset, size in manifest['patches']:
        c.upload(data[offset:offset + size], stage + '/delta')
        c.run(f'dd if={stage}/delta of={stage}/sdvcam bs=1 seek={offset} conv=notrunc 2>/dev/null')
    if c.run(f'md5sum {stage}/sdvcam').split()[0] != target_md5:
        raise RuntimeError('Staged binary checksum mismatch')

    c.run('killall sdvcam')
    time.sleep(1)
    c.run('if pidof sdvcam >/dev/null; then killall -9 sdvcam; fi; true')
    try:
        c.run(f'cat {stage}/sdvcam > /mnt/extsd/sdvcam; cat {stage}/sdvcam > /mnt/extsd/.sdvcam_patched; printf %s {target_md5} > /mnt/extsd/ui_theme/current/enabled; sync')
        c.run('umount /usr/bin/sdvcam; mount --bind /mnt/extsd/.sdvcam_patched /usr/bin/sdvcam')
        if c.run('md5sum /usr/bin/sdvcam').split()[0] != target_md5:
            raise RuntimeError('Live app checksum mismatch')
        c.run(START)
        time.sleep(8)
        if not c.run('pidof sdvcam'):
            raise RuntimeError('Camera app exited')
        with urllib.request.urlopen(c.base + '/cgi-bin/snapshot', timeout=10) as response:
            if not response.read(2) == b'\xff\xd8':
                raise RuntimeError('Snapshot is not a JPEG')
        print('Installed:', target_md5, 'PID:', c.run('pidof sdvcam'), flush=True)
    except Exception:
        c.run('killall -9 sdvcam 2>/dev/null; true')
        c.run(f'cat {backup}/sdvcam_sd > /mnt/extsd/sdvcam; cat {backup}/boot_binary > /mnt/extsd/.sdvcam_patched; cat {backup}/enabled > /mnt/extsd/ui_theme/current/enabled; sync')
        c.run('umount /usr/bin/sdvcam; mount --bind /mnt/extsd/.sdvcam_patched /usr/bin/sdvcam')
        c.run(START)
        raise


if __name__ == '__main__':
    main()

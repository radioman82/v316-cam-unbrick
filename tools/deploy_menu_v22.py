"""Install byte-verified v22 from the live v21 baseline, with an SD-card backup."""
from datetime import datetime
import hashlib
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent / 'streaming'))
from deploy import Camera

ROOT = Path(__file__).resolve().parents[1]


def main():
    camera = Camera('http://192.168.178.199:8080')
    data = (ROOT / 'firmware/sdvcam/sdvcam_menu_v22').read_bytes()
    expected = hashlib.md5(data).hexdigest()
    descriptors = camera.run('for f in /proc/$(pidof sdvcam)/fd/*; do readlink "$f"; done; true')
    if any('/mnt/extsd/DCIM/' in line and line.endswith(('.mp4', '.sec')) for line in descriptors.splitlines()):
        raise SystemExit('Stop recording/playback before replacing the camera application')
    current = camera.run('md5sum /usr/bin/sdvcam').split()[0]
    baseline = '/usr/bin/sdvcam'
    if current != '4154e8520e13711bc70fe9e65d424ec7':
        baseline = camera.run("for f in /mnt/extsd/.control-backup-*/sdvcam_v21; do if [ \"$(md5sum \"$f\" | cut -d' ' -f1)\" = 4154e8520e13711bc70fe9e65d424ec7 ]; then echo \"$f\"; break; fi; done")
        if not baseline:
            raise SystemExit(f'No verified v21 backup available, current {current}')
    backup = '/mnt/extsd/.control-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S')
    stage = backup + '/sdvcam_v22'
    camera.run(f'mkdir -p {backup}; cp /usr/bin/sdvcam {backup}/sdvcam_previous; cp /mnt/extsd/.sdvcam_patched {backup}/boot_binary; cp {baseline} {stage}')
    if current == '4154e8520e13711bc70fe9e65d424ec7':
        camera.run(f'cp /usr/bin/sdvcam {backup}/sdvcam_v21')
    print('Backup:', backup, flush=True)
    import base64
    for offset, size in [(0x4afe0, 80), (0x4b83c, 4), (0x4bc0e, 4), (0x4bc90, 4), (0x4c9d4, 4), (0x56dc4, 4), (0x575e4, 4), (0x576a2, 4), (0x23ad84, 232)]:
        chunk = base64.b64encode(data[offset:offset + size]).decode()
        camera.run(f'printf %s {chunk} | /mnt/extsd/bin/busybox base64 -d | dd of={stage} bs=1 seek={offset} conv=notrunc 2>/dev/null')
    assert camera.run(f'md5sum {stage}').split()[0] == expected
    helper = (ROOT / 'firmware/streaming/v316cm-control').read_bytes()
    camera.upload(helper, backup + '/v316cm-control')
    camera.run(f'chmod 755 {backup}/v316cm-control {stage}; mv {backup}/v316cm-control /mnt/extsd/bin/v316cm-control; sync')
    # The native helper is read-only until an explicit action is supplied.
    # pid is checked by the existing shell; no flash partitions are touched.
    camera.run('killall sdvcam')
    time.sleep(1)
    camera.run('if pidof sdvcam >/dev/null; then killall -9 sdvcam; fi')
    try:
        camera.run(f'cat {stage} > /mnt/extsd/sdvcam; cat {stage} > /mnt/extsd/.sdvcam_patched; sync')
        camera.run('umount /usr/bin/sdvcam; mount --bind /mnt/extsd/.sdvcam_patched /usr/bin/sdvcam')
        assert camera.run('md5sum /usr/bin/sdvcam').split()[0] == expected
        camera.run('FB_SYNC=1 SCREEN_INFO=240x376-32bpp LD_HWCAP_MASK=0x00000000 /usr/bin/sdvcam >/tmp/sdvcam.log 2>&1 </dev/null &')
        time.sleep(5)
        print(camera.run('/mnt/extsd/bin/v316cm-control status'))
    except Exception:
        camera.run('killall -9 sdvcam 2>/dev/null || true')
        camera.run(f'cat {backup}/sdvcam_previous > /mnt/extsd/sdvcam; cat {backup}/boot_binary > /mnt/extsd/.sdvcam_patched; sync')
        camera.run('umount /usr/bin/sdvcam; mount --bind /mnt/extsd/.sdvcam_patched /usr/bin/sdvcam')
        camera.run('FB_SYNC=1 SCREEN_INFO=240x376-32bpp LD_HWCAP_MASK=0x00000000 /usr/bin/sdvcam >/tmp/sdvcam.log 2>&1 </dev/null &')
        raise


if __name__ == '__main__':
    main()

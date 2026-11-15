"""Verify installed startup, complete rootfs, completed package and stable app PID."""
import argparse
import hashlib
import json
from pathlib import Path

from camera_uart import CameraUART


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    args = p.parse_args()
    manifest = json.loads((args.folder / 'manifest.json').read_text())
    image = (args.folder / 'V316CM_STARTUP_NEU1_PRIVATE_16MiB.bin').read_bytes()
    wav = Path(manifest['wav_source']).read_bytes()
    package = (args.folder / 'firmware-update.bin').read_bytes()
    assert hashlib.sha256(image).hexdigest() == manifest['sha256']
    assert hashlib.sha256(wav).hexdigest() == manifest['wav_sha256']
    expected = [hashlib.md5(data).hexdigest() for data in (wav, image[0x400000:0xe80000], package)]
    c = CameraUART()
    try:
        result = c.run('md5sum /usr/share/minigui/res/audio/startup.wav /dev/mtdblock2 /mnt/extsd/firmware-update.done', 30)
        actual = [line.split()[0] for line in result.splitlines()]
        assert actual == expected, (actual, expected)
        first = c.run('ps w | grep [s]dvcam', 10).splitlines()
        assert len(first) == 1 and '/usr/bin/sdvcam' in first[0]
        second = c.run('sleep 10; ps w | grep [s]dvcam', 20).splitlines()
        assert first == second
        log = c.run('tail -6 /mnt/extsd/firmware-update.log', 10)
        assert 'UPDATE ERFOLGREICH' in log
        report = {'status': 'installed and verified after reboot', 'startup_md5': actual[0], 'rootfs_md5': actual[1], 'completed_package_md5': actual[2], 'sdvcam_pid': first[0].split()[0], 'sdvcam_stable_across_checks': True, 'updater_log': log, 'listening_test': 'not performed by agent'}
        (args.folder / 'verification.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2), flush=True)
    finally:
        c.close()


if __name__ == '__main__':
    main()

"""Install the WLAN importer over COM11; preserve credentials in the overlay.

Does not start an import or flash firmware. Backup folder must be new/private.
"""
import argparse
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from camera_uart import CameraUART
from sd_update.deploy import upload

HERE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--backup', type=Path, required=True)
    p.add_argument('--enable-boot', action='store_true', help='Enable experimental boot import after device tests')
    args = p.parse_args()
    args.backup.mkdir(parents=True, exist_ok=False)
    c = CameraUART()
    locked = False
    targets = {
        '/opt/cam/wlan/wlan-import': args.binary.read_bytes(),
        **{'/opt/cam/wlan/'+name: (HERE/name).read_bytes() for name in ('connect.sh','dhcp.sh','import.sh')},
        **{'/opt/cam/'+name: (HERE/name).read_bytes() for name in ('start_streaming.sh','stop_streaming.sh')},
    }
    if args.enable_boot:
        targets['/etc/init.d/S99wlan'] = (HERE/'init.sh').read_bytes()
    try:
        c.run('test -d /overlay/upperdir && test ! -d /tmp/v316-sd-update.lock && test ! -f /mnt/extsd/firmware-update.bin')
        (args.backup/'wlan.conf').write_bytes(c.read('/data/wlan.conf'))
        for target in targets:
            if c.run(f'if [ -f {target} ]; then echo yes; fi') == 'yes':
                (args.backup/target.replace('/','_')).write_bytes(c.read(target))
        c.run('mkdir -p /tmp/v316-wlan-stage /opt/cam/wlan')
        stages = {}
        for index, (target, data) in enumerate(targets.items()):
            stage = f'/tmp/v316-wlan-stage/{index}'
            upload(c, data, stage)
            c.run(f'chmod 755 {stage}')
            if target.endswith('.sh') or target.endswith('/S99wlan'):
                c.run(f'{c.busybox} sh -n {stage}')
            stages[target] = stage
        helper = stages['/opt/cam/wlan/wlan-import']
        c.run(f'{helper} --check /data/wlan.conf')
        c.run('mkdir /tmp/v316cm-network-lock')
        locked = True
        for target, data in targets.items():
            c.run(f'cp {stages[target]} {target}.new && chmod 755 {target}.new && mv {target}.new {target}')
            assert c.run(f'md5sum {target}').split()[0] == hashlib.md5(data).hexdigest(), target
        c.run('/opt/cam/wlan/wlan-import --normalize /data/wlan.conf /data/wlan.conf; sync')
        assert c.run(f'{c.busybox} stat -c %a /data/wlan.conf').strip() == '600'
        print('WLAN importer installed; existing configuration preserved. No import started.')
    finally:
        if locked:
            c.run('rmdir /tmp/v316cm-network-lock')
        c.run('rm -f /tmp/v316-wlan-stage/* /tmp/v316-update-upload.gz; rmdir /tmp/v316-wlan-stage 2>/dev/null; true')
        c.close()


if __name__ == '__main__':
    main()

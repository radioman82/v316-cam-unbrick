"""Install the one-time SD-update bridge over COM11, without starting a flash.

Only for the verified standalone camera. Source and destination hashes are
checked. A private backup is required; no firmware or WLAN data is published.
"""
import argparse
import base64
import gzip
import hashlib
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from camera_uart import CameraUART

HERE = Path(__file__).resolve().parent


def upload(c, data, destination):
    packed = gzip.compress(data)
    c.run(': > /tmp/v316-update-upload.gz')
    for start in range(0, len(packed), 1536):
        chunk = base64.b64encode(packed[start:start+1536]).decode()
        c.run(f'printf %s {chunk} | {c.busybox} base64 -d >> /tmp/v316-update-upload.gz')
    c.run(f'{c.busybox} gzip -dc /tmp/v316-update-upload.gz > {destination}')
    actual = c.run(f'md5sum {destination}').split()[0]
    if actual != hashlib.md5(data).hexdigest():
        raise RuntimeError(f'Upload checksum mismatch: {destination}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--updater', type=Path, required=True)
    p.add_argument('--backup', type=Path, required=True)
    p.add_argument('--install-bootstrap', action='store_true', help='Enable the boot-time hook, effective next boot')
    args = p.parse_args()
    args.backup.mkdir(parents=True, exist_ok=False)
    c = CameraUART()
    try:
        c.run('test -x /opt/cam/bin/busybox && test -x /usr/bin/sdvcam && test -d /overlay/upperdir')
        for name in ('setting.lua',):
            (args.backup/name).write_bytes(c.read('/data/'+name))
        for remote, local in (('/opt/cam/update/updater', 'updater'),
                              ('/opt/cam/update/sd_update.sh', 'sd_update.sh'),
                              ('/etc/init.d/S02sdupdate', 'S02sdupdate')):
            if c.run(f'if [ -f {remote} ]; then echo yes; fi') == 'yes':
                (args.backup/local).write_bytes(c.read(remote))
        c.run('mkdir -p /tmp/v316-update-stage /opt/cam/update')
        for name, data in (('updater', args.updater.read_bytes()),
                           ('sd_update.sh', (HERE/'sd_update.sh').read_bytes())):
            upload(c, data, '/tmp/v316-update-stage/'+name)
        c.run(f'{c.busybox} sh -n /tmp/v316-update-stage/sd_update.sh')
        for name, data in (('updater', args.updater.read_bytes()),
                           ('sd_update.sh', (HERE/'sd_update.sh').read_bytes())):
            target = '/opt/cam/update/'+name
            actual = c.run(f'if [ -f {target} ]; then md5sum {target}; fi')
            if actual and actual.split()[0] == hashlib.md5(data).hexdigest():
                continue
            try:
                c.run(f'cp /tmp/v316-update-stage/{name} {target}.new && chmod 755 {target}.new && mv {target}.new {target}')
            except Exception:
                c.run(f'rm -f {target}.new; sync')
                raise
        if args.install_bootstrap:
            upload(c, (HERE/'bootstrap.sh').read_bytes(), '/tmp/v316-update-stage/S02sdupdate')
            c.run('cp /tmp/v316-update-stage/S02sdupdate /etc/init.d/S02sdupdate.new && chmod 755 /etc/init.d/S02sdupdate.new && mv /etc/init.d/S02sdupdate.new /etc/init.d/S02sdupdate')
        c.run('sync')
        print('BRIDGE_INSTALLED_NO_FLASH_STARTED', flush=True)
    finally:
        c.close()


if __name__ == '__main__':
    main()

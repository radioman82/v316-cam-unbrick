"""Stage and preflight a verified package via a temporary camera FTP listener."""
import argparse
import ftplib
import hashlib
from pathlib import Path

from camera_uart import CameraUART


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path)
    p.add_argument('host')
    args = p.parse_args()
    data = args.package.read_bytes()
    c = CameraUART()
    pid = None
    try:
        c.run('test -d /mnt/extsd && mount | grep -q " on /mnt/extsd type vfat " && test ! -e /mnt/extsd/firmware-update.bin && test ! -e /mnt/extsd/firmware-update.installing && test ! -e /mnt/extsd/.codex-neu1-upload')
        pid = c.run('/opt/cam/bin/busybox tcpsvd -E 0.0.0.0 18021 /opt/cam/bin/busybox ftpd -w -A /mnt/extsd >/tmp/codex-rescue-ftp.log 2>&1 </dev/null & echo $!').splitlines()[-1]
        assert pid.isdigit()
        with ftplib.FTP() as ftp:
            ftp.connect(args.host, 18021, timeout=30)
            ftp.login()
            with args.package.open('rb') as source:
                ftp.storbinary('STOR .codex-neu1-upload', source, blocksize=65536)
        digest = c.run('sync; md5sum /mnt/extsd/.codex-neu1-upload', 30).split()[0]
        assert digest == hashlib.md5(data).hexdigest()
        print('UPLOAD_MD5_VERIFIED', digest, flush=True)
        print(c.run('/opt/cam/update/updater --preflight /mnt/extsd/.codex-neu1-upload', 60), flush=True)
        c.run('test ! -e /mnt/extsd/firmware-update.bin && mv /mnt/extsd/.codex-neu1-upload /mnt/extsd/firmware-update.bin && sync')
        print('STAGED_NOT_YET_INSTALLED', flush=True)
    finally:
        if pid:
            c.run(f'kill {pid} 2>/dev/null; true')
        c.close()


if __name__ == '__main__':
    main()

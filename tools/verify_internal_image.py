"""Verify the offline rootfs and probe kernel XZ support without flashing."""
import base64
import hashlib
from pathlib import Path
import re
import struct
import subprocess
import zlib
from camera_uart import CameraUART
from build_internal_image import WORK,TOOLS,ROOT,recover_setting

def main():
    image=(WORK/'V316CM_STANDALONE_16MiB.bin').read_bytes()
    assert len(image)==16777216
    assert image[0x400000:0x400004]==b'hsqs'
    assert image[0xe80000:0xf00000]==b'\xff'*0x80000
    sq=WORK/'standalone.squashfs'
    listing=subprocess.check_output([str(TOOLS/'unsquashfs.exe'),'-ll',str(sq)]).decode()
    (WORK/'standalone-listing.txt').write_text(listing)
    links={line.split(' squashfs-root/',1)[1] for line in listing.splitlines() if line.startswith('l')}
    original={line.split(' squashfs-root/',1)[1] for line in (WORK/'reference-listing.txt').read_text().splitlines() if line.startswith('l')}
    assert links==original, 'Symlinks changed'
    for path in ('dev/console','dev/null','dev/ttyS0'):
        assert any(line.startswith('c') and line.endswith('squashfs-root/'+path) for line in listing.splitlines())
    print('METADATA_OK',len(links),'symlinks, 3 device nodes',flush=True)
    verify=WORK/'verify-rootfs'
    subprocess.run([str(TOOLS/'unsquashfs.exe'),'-force','-no-progress','-d',str(verify),str(sq)],check=True)
    root=WORK/'rootfs'
    count=0
    for p in root.rglob('*'):
        if not p.is_file():continue
        other=verify/p.relative_to(root)
        assert p.read_bytes()==other.read_bytes(),str(p)
        count+=1
    print('CONTENT_OK',count,'files including Cygwin symlinks',flush=True)
    # Resolve dependencies by names; the filesystem carries the original linker links.
    libs={p.name for p in root.rglob('*') if p.is_file()}
    missing=[]
    for p in root.rglob('*'):
        if not p.is_file():continue
        b=p.read_bytes()
        if b[:5]!=b'\x7fELF\x01':continue
        off=struct.unpack_from('<I',b,32)[0]
        size,num=struct.unpack_from('<HH',b,46)
        if not off:continue
        sections=[struct.unpack_from('<10I',b,off+i*size) for i in range(num)]
        for s in sections:
            if s[1]!=6:continue
            strings=sections[s[6]]
            tab=b[strings[4]:strings[4]+strings[5]]
            for i in range(s[4],s[4]+s[5],8):
                kind,value=struct.unpack_from('<II',b,i)
                if kind==1:
                    name=tab[value:].split(b'\0')[0].decode()
                    if name not in libs:missing.append((str(p.relative_to(root)),name))
    assert not missing,missing
    print('ELF_DEPENDENCIES_OK',flush=True)
    for p in [root/'etc/init.d/S01app',*list((root/'opt/cam').glob('*.sh')),*list((root/'opt/cam/www/cgi-bin').iterdir())]:
        assert '/mnt/extsd' not in p.read_text(),p
    print('INTERNAL_START_PATHS_OK',flush=True)
    # Tiny independent loop mount proves XZ support on the running kernel.
    probe=WORK/'xz-probe-source'
    probe.mkdir(exist_ok=True)
    (probe/'proof').write_text('V316_XZ_PROBE_OK\n')
    target=WORK/'xz-probe.squashfs'
    subprocess.run([str(TOOLS/'mksquashfs.exe'),str(probe),str(target),'-noappend','-comp','xz','-b','131072','-Xdict-size','131072','-no-xattrs','-all-root','-no-progress'],check=True,stdout=subprocess.DEVNULL)
    c=CameraUART()
    try:
        data=target.read_bytes()
        remote='/tmp/v316-xz-probe.squashfs'
        c.run(f': > {remote}')
        for i in range(0,len(data),1536):
            chunk=base64.b64encode(data[i:i+1536]).decode()
            c.run(f'printf %s {chunk} | /mnt/extsd/bin/busybox base64 -d >> {remote}')
        assert c.run(f'md5sum {remote}').split()[0]==hashlib.md5(data).hexdigest()
        c.run('mkdir -p /tmp/v316-xz-mount')
        c.run(f'mount -t squashfs -o loop,ro {remote} /tmp/v316-xz-mount')
        assert c.run('cat /tmp/v316-xz-mount/proof')=='V316_XZ_PROBE_OK'
        c.run('umount /tmp/v316-xz-mount')
        print('LIVE_KERNEL_XZ_MOUNT_OK',flush=True)
    finally:c.close()
    print('VERIFIED_OFFLINE_IMAGE_NOT_DEVICE_BOOT_TESTED',flush=True)

if __name__=='__main__':main()

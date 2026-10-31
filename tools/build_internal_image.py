"""Build a standalone camera filesystem from the known-good SPI image."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import stat
import struct
import zlib

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent/'internal-image-build'
TOOLS=ROOT.parent/'Tools/Scripts/unfex-refex-fwinfo-V316-Windows/squashfs_tools'
REFERENCE=ROOT/'firmware/V316CM_WORKING_FULL_IMAGE_16MB.bin'

def prepare():
    WORK.mkdir(exist_ok=True)
    data=REFERENCE.read_bytes()
    assert len(data)==16777216
    assert hashlib.sha256(data).hexdigest()=='14c77033fb837671dfd8948860c7d081e8401a5d0f3880be1a6a18f485a46de8'
    sq=WORK/'reference.squashfs'
    sq.write_bytes(data[0x400000:0xe80000])
    listing=subprocess.check_output([str(TOOLS/'unsquashfs.exe'),'-ll',str(sq)])
    (WORK/'reference-listing.txt').write_bytes(listing)
    subprocess.run([str(TOOLS/'unsquashfs.exe'),'-s',str(sq)],check=True)
    dest=WORK/'rootfs'
    if not dest.exists():
        subprocess.run([str(TOOLS/'unsquashfs.exe'),'-no-progress','-d',str(dest),str(sq)],check=True)

def recover_setting(image):
    """Recover CRC-valid setting.lua fragments from a saved JFFS2 partition."""
    names=[]
    nodes=[]
    def crc32(data):return zlib.crc32(data,0xffffffff)^0xffffffff
    for off in range(0,len(image)-68,4):
        if image[off:off+2]!=b'\x85\x19':continue
        magic,kind,size,crc=struct.unpack_from('<HHII',image,off)
        n=image[off:off+size]
        if len(n)!=size or crc32(n[:8])!=crc:continue
        if kind==0xe001 and len(n)>=40:
            if crc32(n[:32])!=struct.unpack_from('<I',n,32)[0]:continue
            name=n[40:40+n[28]]
            if crc32(name)!=struct.unpack_from('<I',n,36)[0]:continue
            if name==b'setting.lua':names.append((struct.unpack_from('<I',n,16)[0],struct.unpack_from('<I',n,20)[0]))
        elif kind==0xe002 and len(n)>=68:
            if crc32(n[:60])!=struct.unpack_from('<I',n,64)[0]:continue
            data=n[68:68+struct.unpack_from('<I',n,48)[0]]
            if crc32(data)!=struct.unpack_from('<I',n,60)[0]:continue
            if n[56]==6:data=zlib.decompress(data)
            elif n[56]!=0:continue
            nodes.append((struct.unpack_from('<I',n,12)[0],struct.unpack_from('<I',n,16)[0],struct.unpack_from('<I',n,28)[0],struct.unpack_from('<I',n,44)[0],data))
    if not names:return None
    ino=max(names)[1]
    pieces=sorted((n for n in nodes if n[0]==ino),key=lambda n:n[1])
    if not pieces:return None
    result=bytearray(pieces[-1][2])
    covered=bytearray(len(result))
    for _,_,_,off,data in pieces:
        end=min(len(result),off+len(data))
        if off<end:result[off:end]=data[:end-off];covered[off:end]=b'\x01'*(end-off)
    return bytes(result) if all(covered) else None

def assemble():
    dest=WORK/'rootfs'
    runtime=WORK/'runtime'
    assert runtime.is_dir()
    ui=ROOT/'firmware/ui_internal'
    # Replace files in their normal resource locations, removing all SD mounts.
    def put(source,target):
        target=dest/target
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    def tree(source,target):
        for p in source.rglob('*'):
            if p.is_file():put(p,str(Path(target)/p.relative_to(source)))
    tree(runtime/'custom_ui','usr/share/minigui/res/images')
    tree(ui/'images','usr/share/minigui/res/images')
    put(ROOT/'firmware/splash/byebye.bmp','usr/share/minigui/res/images/shutdown.bmp')
    tree(ui/'layout','usr/share/minigui/res/layout')
    put(ui/'zh-DE.xml','usr/share/minigui/res/lang/zh-DE.xml')
    put(ui/'sdvcam_menu_v23','usr/bin/sdvcam')
    for folder in ('bin','lib','www'):
        tree(runtime/folder,'opt/cam/'+folder)
    for name in ('start_streaming.sh','stop_streaming.sh','network_mode.sh'):
        text=(runtime/name).read_text().replace('/mnt/extsd','/opt/cam')
        text=text.replace('/opt/cam/wlan.conf','/data/wlan.conf')
        text=text.replace('# Read configuration from SD card','# Read persistent internal WLAN configuration')
        (dest/'opt/cam'/name).write_text(text,encoding='utf-8',newline='\n')
    for p in (dest/'opt/cam/www/cgi-bin').iterdir():
        p.write_text(p.read_text().replace('/mnt/extsd','/opt/cam'),encoding='utf-8',newline='\n')
    put(runtime/'wlan.conf','data/wlan.conf')
    # Recover valid settings from the pre-existing rescue snapshot, not corrupt live files.
    rescue_path=ROOT.parent/'recovery-2026-10-29/V316CM_CURRENT_WORKING_20261029_16MB.bin'
    rescue=rescue_path.read_bytes() if rescue_path.exists() else None
    current=sorted(ROOT.parent.glob('recovery-internal-*/mtd3.bin'))
    setting=recover_setting(current[-1].read_bytes()) if current else None
    setting_source='current CRC-valid JFFS2 snapshot'
    if not setting and rescue:
        setting=recover_setting(rescue[0xe80000:0xf00000])
        setting_source='2026-10-29 rescue snapshot'
    if setting:
        (dest/'data/setting.lua').write_bytes(setting)
    import re
    p=dest/'data/setting.lua'
    text=p.read_text(encoding='utf-8')
    text,count=re.subn(r'((?:\["ml_device_language"\]|\bml_device_language)\s*=\s*)\d+',r'\g<1>6',text)
    assert count==1
    p.write_text(text,encoding='utf-8',newline='\n')
    # Keep hardware/QoS setup, eliminate the stock SD binary-copy/update logic.
    p=dest/'etc/init.d/S01app'
    original=(WORK/'stock-S01app').read_text() if (WORK/'stock-S01app').exists() else p.read_text()
    (WORK/'stock-S01app').write_text(original)
    head=original.split('    # /usr/bin/tinymix')[0]
    head=head.replace('/mnt/extsd/core.%e.%p','/tmp/core.%e.%p')
    body='''    mkdir -p /tmp/v316-data /tmp/event
    /usr/bin/sdvcam >/tmp/sdvcam.log 2>&1 </dev/null &
    hwclock --hctosys
}
stop() {
    hwclock --systohc
    killall sdvcam 2>/dev/null
}
case "$1" in
    start) start ;;
    stop) stop ;;
    restart) stop; sleep 1; start ;;
    *) exit 1 ;;
esac
exit 0
'''
    p.write_text(head+body,encoding='utf-8',newline='\n')
    # mksquashfs reads Cygwin symlink metadata; restore missing device nodes
    # and explicit UNIX modes rather than depending on Windows ACL defaults.
    pseudo=[]
    for line in (WORK/'reference-listing.txt').read_text().splitlines():
        if ' squashfs-root/' not in line:continue
        attr=line[:10]
        path=line.split(' squashfs-root/',1)[1].split(' -> ',1)[0]
        mode=sum((1 << (8-i)) for i,ch in enumerate(attr[1:]) if ch not in '-ST')
        if attr[3] in 'sS':mode|=stat.S_ISUID
        if attr[6] in 'sS':mode|=stat.S_ISGID
        if attr[9] in 'tT':mode|=stat.S_ISVTX
        if attr[0]=='c':
            fields=line.split(' squashfs-root/',1)[0].split()
            major=int(fields[2].rstrip(','));minor=int(fields[3])
            pseudo.append(f'{path} c {mode:o} 0 0 {major} {minor}')
        elif attr[0] in '-d' and (dest/path).exists():
            pseudo.append(f'{path} m {mode:o} 0 0')
    # Newly added runtime tools and scripts must have executable bits.
    for p in (dest/'opt').rglob('*'):
        path=p.relative_to(dest).as_posix()
        mode='755' if p.is_dir() or '/bin/' in path or '/cgi-bin/' in path or p.suffix=='.sh' else '644'
        pseudo.append(f'{path} m {mode} 0 0')
    if not any(line.startswith('opt m ') for line in pseudo):pseudo.append('opt m 755 0 0')
    pseudo.append('data/wlan.conf m 600 0 0')
    pf=WORK/'modes.pseudo'
    pf.write_text('\n'.join(pseudo)+'\n')
    sq=WORK/'standalone.squashfs'
    subprocess.run([str(TOOLS/'mksquashfs.exe'),str(dest),str(sq),'-noappend','-comp','xz','-b','131072','-Xdict-size','131072','-no-xattrs','-all-root','-no-progress','-pf',str(pf)],check=True)
    print('ROOTFS_BYTES',sq.stat().st_size,'BUDGET',0xa80000,flush=True)
    if sq.stat().st_size>0xa80000:
        raise RuntimeError('Root filesystem exceeds unchanged partition size')
    data=bytearray(REFERENCE.read_bytes())
    data[0x400000:0xe80000]=sq.read_bytes().ljust(0xa80000,b'\xff')
    data[0xe80000:0xf00000]=b'\xff'*0x80000
    welcome=(ROOT/'firmware/splash/welcome.bmp').read_bytes()
    data[0xf20000:0xf20000+len(welcome)]=welcome
    target=WORK/'V316CM_STANDALONE_16MiB.bin'
    target.write_bytes(data)
    manifest={'sha256':hashlib.sha256(data).hexdigest(),'rootfs_bytes':sq.stat().st_size,'rootfs_limit':0xa80000,'settings_recovered':bool(setting),'setting_source':setting_source if setting else 'factory defaults with German language','status':'built, not flashed or device-tested','private':'contains device WLAN configuration'}
    (WORK/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('IMAGE_BUILT',target,manifest['sha256'],flush=True)

def sizes():
    import gzip
    rows=[]
    for f in (WORK/'rootfs').rglob('*'):
        if not f.is_file():continue
        b=f.read_bytes()
        rows.append((len(gzip.compress(b)),len(b),f.relative_to(WORK/'rootfs').as_posix()))
    for row in sorted(rows,reverse=True)[:45]:print(row)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--assemble',action='store_true')
    parser.add_argument('--sizes',action='store_true')
    parser.add_argument('--work-dir',type=Path,default=WORK)
    parser.add_argument('--squashfs-tools',type=Path,default=TOOLS)
    args=parser.parse_args()
    WORK=args.work_dir.resolve()
    TOOLS=args.squashfs_tools.resolve()
    prepare()
    if args.assemble:assemble()
    if args.sizes:sizes()

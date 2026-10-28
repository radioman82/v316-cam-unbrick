"""Stage v23 and its resources, verify checksums, restart with automatic rollback."""
import base64
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import time
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'streaming'))
from deploy import Camera

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'firmware/ui_theme'
BASE='/mnt/extsd/ui_theme/v22-base'
CURRENT='/mnt/extsd/ui_theme/current'
START='FB_SYNC=1 SCREEN_INFO=240x376-32bpp LD_HWCAP_MASK=0x00000000 /usr/bin/sdvcam >/tmp/sdvcam.log 2>&1 </dev/null &'


def main():
    c=Camera('http://192.168.178.199:8080')
    manifest=json.loads((OUT/'manifest.json').read_text())
    data=(OUT/'sdvcam_menu_v23').read_bytes()
    assert hashlib.md5(data).hexdigest()==manifest['md5']
    pid=c.run('pidof sdvcam')
    descriptors=c.run(f'for f in /proc/{pid}/fd/*; do readlink "$f"; done; true')
    if any('/DCIM/' in x and x.endswith(('.mp4','.sec')) for x in descriptors.splitlines()):
        raise SystemExit('Stop recording/playback before updating the camera UI')
    actual=c.run('md5sum /usr/bin/sdvcam').split()[0]
    c.run('mkdir -p /mnt/extsd/ui_theme')
    if actual==manifest['baseline']:
        c.run(f'cp /usr/bin/sdvcam {BASE}')
    assert c.run(f'md5sum {BASE}').split()[0]==manifest['baseline']
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    backup='/mnt/extsd/.ui-theme-backup-'+stamp
    stage='/mnt/extsd/ui_theme/stage-'+stamp
    c.run(f'mkdir -p {backup} {stage}; cp /usr/bin/sdvcam {backup}/sdvcam_previous; cp /mnt/extsd/.sdvcam_patched {backup}/boot_binary; cp /etc/init.d/S00zsdvcam {backup}/S00zsdvcam; cp -r /usr/share/minigui/res/layout {backup}/layout; cp /usr/share/minigui/res/lang/zh-DE.xml {backup}/zh-DE.xml; cp -r /mnt/extsd/custom_ui {backup}/images; cp {BASE} {stage}/sdvcam')
    network_scripts=('start_streaming.sh','stop_streaming.sh','network_mode.sh')
    c.run(f'mkdir -p {backup}/network; for name in {" ".join(network_scripts)}; do if [ -f /mnt/extsd/$name ]; then cp /mnt/extsd/$name {backup}/network/$name; fi; done')
    print('Backup:',backup,flush=True)
    for off,size in manifest['patches']:
        # Upload just the audited patch regions and the appended renderer.
        c.upload(data[off:off+size],stage+'/delta')
        c.run(f'dd if={stage}/delta of={stage}/sdvcam bs=1 seek={off} conv=notrunc 2>/dev/null')
    assert c.run(f'md5sum {stage}/sdvcam').split()[0]==manifest['md5']
    archive=io.BytesIO()
    with tarfile.open(fileobj=archive,mode='w:gz') as t:
        for folder in ('layout','images'):
            for f in (OUT/folder).iterdir():t.add(f,arcname=folder+'/'+f.name)
        t.add(OUT/'zh-DE.xml',arcname='zh-DE.xml')
        for name in network_scripts:t.add(ROOT/'tools/streaming'/name,arcname='network/'+name)
    c.upload(archive.getvalue(),stage+'/resources.tgz')
    c.run(f'/mnt/extsd/bin/busybox tar -xzf {stage}/resources.tgz -C {stage}; chmod 755 {stage}/sdvcam; sync')
    boot=base64.b64decode(c.run('/mnt/extsd/bin/busybox base64 /etc/init.d/S00zsdvcam')).decode()
    marker='# Allwinner V316 Cam UI theme resources'
    if marker in boot:boot=boot[:boot.index(marker)]+'exit 0\n'
    assert 'exit 0' in boot
    extra=f'''{marker}
if [ -f {CURRENT}/enabled ] && [ -f /mnt/extsd/.sdvcam_patched ] && [ "$(cat {CURRENT}/enabled)" = "$(md5sum /mnt/extsd/.sdvcam_patched | cut -d' ' -f1)" ]; then
    mount --bind {CURRENT}/layout /usr/share/minigui/res/layout 2>>$L
    mount --bind {CURRENT}/zh-DE.xml /usr/share/minigui/res/lang/zh-DE.xml 2>>$L
fi
'''
    boot=boot.replace('exit 0',extra+'exit 0')
    c.upload(boot.encode(),stage+'/S00zsdvcam')
    c.run('killall sdvcam')
    time.sleep(1)
    c.run('if pidof sdvcam >/dev/null; then killall -9 sdvcam; fi')
    try:
        c.run(f'cp {stage}/network/* /mnt/extsd/; chmod 755 /mnt/extsd/start_streaming.sh /mnt/extsd/stop_streaming.sh /mnt/extsd/network_mode.sh; if pidof wpa_supplicant >/dev/null; then touch /tmp/v316cm-stream-mode /tmp/v316cm-stream-ready; fi')
        c.run(f'if [ -d {CURRENT} ]; then mv {CURRENT} {backup}/previous_theme; fi; mkdir -p {CURRENT}; cp -r {stage}/layout {CURRENT}/layout; cp {stage}/zh-DE.xml {CURRENT}/zh-DE.xml; cp {stage}/images/* /mnt/extsd/custom_ui/; printf %s {manifest["md5"]} > {CURRENT}/enabled')
        c.run(f'umount /usr/share/minigui/res/layout 2>/dev/null; umount /usr/share/minigui/res/lang/zh-DE.xml 2>/dev/null; mount --bind {CURRENT}/layout /usr/share/minigui/res/layout; mount --bind {CURRENT}/zh-DE.xml /usr/share/minigui/res/lang/zh-DE.xml')
        c.run(f'cat {stage}/sdvcam > /mnt/extsd/sdvcam; cat {stage}/sdvcam > /mnt/extsd/.sdvcam_patched; sync')
        c.run('umount /usr/bin/sdvcam; mount --bind /mnt/extsd/.sdvcam_patched /usr/bin/sdvcam')
        assert c.run('md5sum /usr/bin/sdvcam').split()[0]==manifest['md5']
        c.run(START)
        time.sleep(8)
        newpid=c.run('pidof sdvcam')
        if not newpid:raise RuntimeError('Camera application exited')
        with urllib.request.urlopen(c.base+'/cgi-bin/snapshot',timeout=10) as r:jpeg=r.read()
        from PIL import Image
        image=Image.open(io.BytesIO(jpeg));image.load()
        assert image.size==(320,240)
        c.run(f'cat {stage}/S00zsdvcam > /etc/init.d/S00zsdvcam; chmod 755 /etc/init.d/S00zsdvcam; sync')
        print('Live PID',newpid,'snapshot',len(jpeg),'bytes',flush=True)
        (OUT/'installed.json').write_text(json.dumps({'backup':backup,'stage':stage,'md5':manifest['md5'],'pid':newpid},indent=2))
    except Exception:
        c.run('killall -9 sdvcam 2>/dev/null; true')
        c.run(f'umount /usr/share/minigui/res/layout 2>/dev/null; umount /usr/share/minigui/res/lang/zh-DE.xml 2>/dev/null; if [ -d {CURRENT} ]; then mv {CURRENT} {stage}/failed_theme; fi; if [ -d {backup}/previous_theme ]; then mv {backup}/previous_theme {CURRENT}; fi; true')
        c.run(f'umount /usr/share/minigui/res/layout 2>/dev/null; umount /usr/share/minigui/res/lang/zh-DE.xml 2>/dev/null; mount --bind {backup}/layout /usr/share/minigui/res/layout; mount --bind {backup}/zh-DE.xml /usr/share/minigui/res/lang/zh-DE.xml; cp {backup}/images/* /mnt/extsd/custom_ui/; cat {backup}/sdvcam_previous > /mnt/extsd/sdvcam; cat {backup}/boot_binary > /mnt/extsd/.sdvcam_patched; cat {backup}/S00zsdvcam > /etc/init.d/S00zsdvcam; sync')
        c.run(f'cp {backup}/network/* /mnt/extsd/; rm -f /tmp/v316cm-stream-mode /tmp/v316cm-stream-ready; true')
        c.run('umount /usr/bin/sdvcam; mount --bind /mnt/extsd/.sdvcam_patched /usr/bin/sdvcam')
        c.run(START)
        raise


if __name__=='__main__':main()

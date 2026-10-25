"""Automatischen Bildschirmschoner auf der Kamera abschalten.

Der Screensaver wird in /data/setting.lua (persistent, Overlay auf jffs2)
gespeichert und beim Start nach /tmp/data/setting.lua kopiert.

ml_camera_autoscreensaver: 0 = aus, 1 = 30 s, 2 = 1 min, 3 = 2 min

usage: python set_screensaver.py [0|1|2|3]
"""
import serial
import sys
import time

val = sys.argv[1] if len(sys.argv) > 1 else "0"
port = "COM11"

CMDS = [
    "cp /data/setting.lua /mnt/extsd/setting.lua.bak",
    "cp /tmp/data/setting.lua /mnt/extsd/setting_tmp.lua.bak",
    f"sed 's/autoscreensaver\"] = ./autoscreensaver\"] = {val}/' /data/setting.lua > /tmp/s1.lua",
    "cat /tmp/s1.lua > /data/setting.lua",
    f"sed 's/autoscreensaver\"] = ./autoscreensaver\"] = {val}/' /tmp/data/setting.lua > /tmp/s2.lua",
    "cat /tmp/s2.lua > /tmp/data/setting.lua",
    "rm -f /tmp/s1.lua /tmp/s2.lua",
    "sync",
    "grep autoscreensaver /data/setting.lua",
    "grep autoscreensaver /tmp/data/setting.lua",
    "ls -l /mnt/extsd/setting.lua.bak",
]

s = serial.Serial(port, 115200, timeout=3)
for c in CMDS:
    s.reset_input_buffer()
    s.write(c.encode() + b"\n")
    time.sleep(0.8)
    out = b""
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    txt = out.decode("utf-8", errors="replace")
    print(f"$ {c}\n{txt.strip()}\n")
s.close()

#!/usr/bin/env python3
"""Allwinner V316 Cam sdvcam v9 - Setup beim Start + Modus-Auswahl auf der Seitentaste.

Basis: unveraendertes sdvcam_v8 (md5 ee7425e348fc3d35d09ff62fc405860a).

Patches
  256460  02 -> 01                  Startfenster = SettingWindow (ID 1)
  338356  19 46 -> 00 21            WindowManager::Init versteckt Fenster 1 nicht
  310286  fe f7 fb fe -> fe f7 71 fd
                                   0x5bc0e: bl 0x5aa08 (PostMsg 85)
                                        -> bl 0x5a6f4 (ShowModeSelectWindow)
                                    r0 ist dort bereits "this" (PreviewWindow).
                                    Beide Seitentasten (135/136) laufen hier durch.
  334572  98 47 -> 00 bf            USB-Dialog: Show-Aufruf NOP
"""
import hashlib

SRC = "sdvcam_v8"
DST = "sdvcam_menu9.bin"

d = bytearray(open(SRC, "rb").read())
assert len(d) == 3407624

PATCHES = [
    (256460, bytes.fromhex("02"), bytes.fromhex("01"), "Startfenster=1"),
    (338356, bytes.fromhex("1946"), bytes.fromhex("0021"), "Init versteckt #1 nicht"),
    (310286, bytes.fromhex("fef7fbfe"), bytes.fromhex("fef771fd"), "Seitentaste->Modusauswahl"),
    (334572, bytes.fromhex("9847"), bytes.fromhex("00bf"), "USB-Dialog Show NOP"),
]

for off, old, new, why in PATCHES:
    cur = bytes(d[off:off + len(old)])
    if cur != old:
        raise SystemExit("ABBRUCH %s @%d: erwartet %s, gefunden %s"
                         % (why, off, old.hex(), cur.hex()))
    d[off:off + len(new)] = new
    print("ok  %-26s @%-7d %s -> %s" % (why, off, old.hex(" "), new.hex(" ")))

open(DST, "wb").write(d)
print("\n%s  %d Bytes  md5=%s" % (DST, len(d), hashlib.md5(d).hexdigest()))

"""
Build sdvcam_menu_v12: v11 + front-button (keyCode 132) -> shutter (keyCode 130).

PreviewWindow::keyProc @ 0x5b83c dispatches on r5 (keyCode) / r6 (inLongPress).
The top OK button emits 130 -> 0x5ba4a (shutter handler).
The front button emits 132 -> menu/show paths.

Three surgical patches route every "key 132, short press" case to 0x5ba4a:

  A  vaddr 0x5b9a4  bne.w 0x5bae8 -> bne.w 0x5ba4a   (path with [+0x160] != 0)
  B  vaddr 0x5b9c0  bne.w 0x5bae8 -> bne.w 0x5ba4a   (site 1, [+0x160]==0, r0!=0)
  C  vaddr 0x5b9c7  cmp r5,#0x82  -> cmp r5,#0x84     (site 2, [+0x160]==0, r0==0)

Long press of 132 is deliberately left alone (it keeps its original behaviour),
and 130 keeps its own long-press -> poweroff, so the camera never powers off
accidentally from the front button.
"""
import hashlib, sys

SRC = r"d:\v316cm\sdvcam_menu_v11"
DST = r"d:\v316cm\sdvcam_menu_v12"

# (vaddr, expected_old_bytes, new_bytes, comment)
PATCHES = [
    (0x5b9a4, bytes.fromhex("40f0a080"), bytes.fromhex("40f05180"),
     "A: bne.w 0x5bae8 -> bne.w 0x5ba4a"),
    (0x5b9c0, bytes.fromhex("40f09280"), bytes.fromhex("40f04380"),
     "B: bne.w 0x5bae8 -> bne.w 0x5ba4a"),
    (0x5b9c6, bytes.fromhex("82"), bytes.fromhex("84"),
     "C: cmp r5,#0x82 -> cmp r5,#0x84  (imm8 is the first byte of 822d)"),
]

V2F = 0x10000  # vaddr - file offset

with open(SRC, "rb") as f:
    data = bytearray(f.read())

print(f"source : {SRC}")
print(f"  md5  : {hashlib.md5(data).hexdigest()}")
print(f"  size : {len(data)}")

for va, old, new, comment in PATCHES:
    off = va - V2F
    cur = bytes(data[off:off + len(old)])
    if cur != old:
        sys.exit(f"FATAL: {va:#x} has {cur.hex()}, expected {old.hex()} - aborting")
    data[off:off + len(new)] = new
    print(f"  {va:#08x} (off {off:#07x}): {old.hex()} -> {new.hex()}   {comment}")

with open(DST, "wb") as f:
    f.write(data)

md5 = hashlib.md5(data).hexdigest()
print(f"\nwritten: {DST}")
print(f"  md5  : {md5}")
print(f"  size : {len(data)}")
print(f"\nEXPECTED_MD5 = \"{md5}\"")

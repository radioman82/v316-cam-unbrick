"""
Build sdvcam_menu_v13 = v12 + patch D.

v12 patched the three "site" dispatches, but PreviewWindow::keyProc has an
EARLIER gate that runs before them:

    0x5b888: r3 = [r4,#0x17c]
    0x5b88c: cbz r3, 0x5b8c6          ; [+0x17c]==0 -> normal dispatch
    0x5b88e: r3 = r5 - 0x3b ; cmp r3,#2 ; bls 0x5b8c6
    0x5b896: cmp r5, #0x84             ; key == 132 ?
    0x5b898: bne 0x5b89e               ; not 132 -> 0x5b89e
    0x5b89a: cmp r6, #1                ; inLongPress == 1 ?
    0x5b89c: beq 0x5b8c6               ; 132 + LONG -> 0x5b8c6
    0x5b89e: r3 = [r4,#0x160]
    0x5b8a2: cbz r3, 0x5b8b0
    0x5b8a4: -> 0x5ba3c (Show menu)    ; 132 + SHORT -> opens the menu

Whenever [+0x17c] != 0 and [+0x160] != 0 (which is the normal preview state)
the front button therefore always opened the menu and never reached the
patched sites. That is exactly the "manchmal schliesst es sich, aber nicht
immer" behaviour seen in the log.

Patch D inverts the long/short test at 0x5b89a/0x5b89c so that a SHORT press
of 132 goes to 0x5ba4a (the shutter handler that key 130 uses):

    0x5b89a: cmp r6,#1  -> cmp r6,#0
    0x5b89c: beq 0x5b8c6 -> beq 0x5ba4a

Result: front button short press -> CloseTopWindow() (closes the tile menu
if open) -> PostMsg(self,self,81,1) = shutter. Long press keeps its own path.
"""
import hashlib, sys

SRC = r"d:\v316cm\sdvcam_menu_v12"
DST = r"d:\v316cm\sdvcam_menu_v13"

PATCHES = [
    (0x5b89a, bytes.fromhex("012e"), bytes.fromhex("002e"),
     "D1: cmp r6,#1 -> cmp r6,#0"),
    (0x5b89c, bytes.fromhex("13d0"), bytes.fromhex("d5d0"),
     "D2: beq 0x5b8c6 -> beq 0x5ba4a"),
]

V2F = 0x10000

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
print(f'\nEXPECTED_MD5 = "{md5}"')

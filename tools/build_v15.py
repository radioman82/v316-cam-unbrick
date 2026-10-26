#!/usr/bin/env python3
"""Build sdvcam_menu_v15:
1. Fix Setup tile in dispatcher: calls Close() and posts MSG 74 (opens SettingWindow).
2. Fix OK shutter in Foto mode: 0x5be08 branches directly to 0x5be6a (PostMsg 81) instead of falling into tile fallback.

Base: sdvcam_menu_v11 (MD5 0ff4ffd99cb8377d9fe28cecc34d5dde)
"""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..", "firmware", "sdvcam", "sdvcam_menu_v11")
OUT = os.path.join(HERE, "..", "firmware", "sdvcam", "sdvcam_menu15.bin")

with open(BASE, "rb") as f:
    data = bytearray(f.read())

assert len(data) == 3407624
base_md5 = hashlib.md5(data).hexdigest()
print(f"Base MD5: {base_md5}")
assert base_md5 == "0ff4ffd99cb8377d9fe28cecc34d5dde"

# 1. New 4-tile dispatcher at 0x5afe0 (file offset 0x4afe0, length 80)
# Disassembly:
# 0x05afe0: 30b5     push {r4, r5, lr}
# 0x05afe2: 0446     mov  r4, r0
# 0x05afe4: 1546     mov  r5, r2
# 0x05afe6: d4f81401 ldr.w r0, [r4, #0x114]
# 0x05afea: 0ef0dffb bl   0x697ac            ; Close FunctionSelectWindow
# 0x05afee: 032d     cmp  r5, #3
# 0x05aff0: 09d0     beq  0x5b006            ; Setup
# 0x05aff2: 022d     cmp  r5, #2
# 0x05aff4: 0ed0     beq  0x5b014            ; Stream
# 0x05aff6: 0422     movs r2, #4             ; Foto (mode 4)
# 0x05aff8: 002d     cmp  r5, #0
# 0x05affa: 00d0     beq  0x5affe
# 0x05affc: 0022     movs r2, #0             ; Video (mode 0)
# 0x05affe: 2046     mov  r0, r4
# 0x05b000: fff7a8fd bl   0x5ab54            ; ModeChangeProc
# 0x05b004: 30bd     pop  {r4, r5, pc}
# 0x05b006: 0123     movs r3, #1
# 0x05b008: 4a22     movs r2, #0x4a          ; MSG 74 = Open SettingWindow
# 0x05b00a: 2146     mov  r1, r4
# 0x05b00c: 2046     mov  r0, r4
# 0x05b00e: fff7fbfc bl   0x5aa08            ; PostMsg(self, self, 74, 1)
# 0x05b012: 30bd     pop  {r4, r5, pc}
# 0x05b014: 43f2a220 movw r0, #0x32a2        ; streaming string
# 0x05b018: c0f22000 movt r0, #0x20
# 0x05b01c: c1f796ec blx  0x1c94c            ; system(...)
# 0x05b020: 30bd     pop  {r4, r5, pc}

DISP_CODE = bytes.fromhex(
    "30b504461546d4f814010ef0dffb032d09d0022d0ed00422002d00d000222046fff7a8fd30bd01234a2221462046fff7fbfc30bd43f2a220c0f22000c1f796ec30bd"
)
DISP_PADDED = DISP_CODE.ljust(80, b"\x00")
assert len(DISP_PADDED) == 80

DISP_OFFSET = 0x5AFE0 - 0x10000
data[DISP_OFFSET:DISP_OFFSET + 80] = DISP_PADDED
print("Applied Patch 1: Dispatcher with SettingWindow fix (80 bytes)")

# 2. Foto-shutter at 0x5be08 (file offset 0x4be08):
# old: 78 bb 3c e0 (cbnz r0, #0x5be6a; b #0x5be86)
# new: 2f e0 00 bf (b #0x5be6a; nop)
SHUTTER_OFFSET = 0x5BE08 - 0x10000
cur_shutter = bytes(data[SHUTTER_OFFSET:SHUTTER_OFFSET + 4])
print("Current bytes at 0x5be08:", cur_shutter.hex())
assert cur_shutter == bytes.fromhex("78bb3ce0"), f"Unexpected bytes: {cur_shutter.hex()}"
data[SHUTTER_OFFSET:SHUTTER_OFFSET + 4] = bytes.fromhex("2fe000bf")
print("Applied Patch 2: Shutter direct jump (4 bytes)")

out_md5 = hashlib.md5(data).hexdigest()
print(f"Output MD5: {out_md5}")

with open(OUT, "wb") as f:
    f.write(data)
print(f"Saved: {OUT}")

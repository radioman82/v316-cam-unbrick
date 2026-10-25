"""
Build sdvcam_menu_v14 = v12 + one branch.

Ziel (User-Spezifikation, "ganz einfach"):

  Vordertaste (keyCode 132):
      aus            -> 1x druecken  = einschalten   (Kernel/PMIC, nicht App)
      laeuft         -> druecken     = Ausloeser (Foto)
      laeuft + lang  -> druecken     = ausschalten

  OK-Taste (keyCode 130): 1x = auswaehlen, 2x schnell = zurueck ins Obermenue
  Seitentasten: navigieren durch die Menues

Der Ausloese-Handler bei 0x5ba4a macht already genau das:
    0x5ba4a: cmp r6,#1
    0x5ba4c: bne 0x5ba6c          ; kurz  -> Ausloeser (PostMsg 81)
    0x5ba4e: ldr r0,[pc,#0x10]    ; "poweroff -f"
    0x5ba52: blx system@plt       ; lang  -> ausschalten
    0x5ba56: b   0x5ba6c

Es fehlt nur die Route dorthin. PreviewWindow::keyProc hat vor den drei
von v12 gepatchten Stellen ein Gate:

    0x5b888: r3 = [r4,#0x17c]
    0x5b88c: cbz r3, 0x5b8c6      ; [+0x17c]==0 -> normale Weiterleitung
    0x5b88e: r3 = r5-0x3b ; cmp r3,#2 ; bls 0x5b8c6
    0x5b896: cmp r5, #0x84        ; Taste 132 (Vorder) ?
    0x5b898: bne 0x5b89e          ; nicht 132 -> 0x5b89e (OK-Taste)
    0x5b89a: cmp r6, #1
    0x5b89c: beq 0x5b8c6          ; 132 + LANG  -> normale Weiterleitung
    0x5b89e: r3 = [r4,#0x160]
    0x5b8a2: cbz r3, 0x5b8b0
    0x5b8a4: -> 0x5ba3c (Show)    ; 132 + KURZ -> Kachelmenue anzeigen

Solange [+0x17c]!=0 und [+0x160]!=0 (das ist der normale Vorschau-Zustand)
landet die Vordertaste also IMMER im Show-Zweig und nie beim Ausloeser.
Genau deshalb schloss sich das Menue "manchmal, aber nicht immer".

PATCH: die 4 Bytes bei 0x5b89a (cmp r6,#1 / beq 0x5b8c6) werden zu einem
einzigen unbedingten Weitensprung auf den Ausloese-Handler ersetzt:

    0x5b89a: b.w 0x5ba4a          ; 00 f0 d6 b8

Danach gilt fuer Taste 132 im Gate - egal ob kurz oder lang:
    kurz -> CloseTopWindow() x3 + PostMsg(self,self,81,1) = AUSLOESER
    lang -> system("poweroff -f")                         = AUSSCHALTEN

Taste 130 (OK) ist nicht betroffen: sie zweigt schon bei 0x5b898
(bne 0x5b89e) vor dem Patch ab und behaelt ihr Menue-Verhalten.
"""
import hashlib, sys

SRC = r"d:\v316cm\sdvcam_menu_v12"
DST = r"d:\v316cm\sdvcam_menu_v14"

PATCHES = [
    (0x5b89a, bytes.fromhex("012e13d0"), bytes.fromhex("00f0d6b8"),
     "E: (cmp r6,#1 / beq 0x5b8c6) -> b.w 0x5ba4a  [Ausloeser/Poweroff]"),
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
print(f'\nEXPECTED_MD5 = "{md5}""')

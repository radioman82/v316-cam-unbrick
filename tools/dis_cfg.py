"""Rekursiver Disassembler fuer sdvcam_v8 (Thumb-2, ARMv7).

objdumps Linear-Sweep verliert in PreviewWindow::keyProc die Synchronisation
(Literal-Pools mitten im Code). Dieses Skript folgt stattdessen den
Verzweigungen ab einer Einsprungadresse und markiert nicht erreichte Bytes
als Daten.

usage: python dis_cfg.py <start_vaddr_hex> [stop_vaddr_hex]
"""
import sys

import capstone

BIN = "sdvcam_v8"
DELTA = 0x10000          # vaddr = datei_offset + 0x10000

with open(BIN, "rb") as f:
    DATA = f.read()

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.skipdata = False
md.detail = True

TERMINATORS = {"bx", "tbb", "tbh", "udf", "svc", "bkpt"}


def read(a, n=4):
    o = a - DELTA
    return DATA[o:o + n]


def disasm_cfg(start, stop):
    seen = {}
    work = [start]
    while work:
        a = work.pop()
        while start <= a < stop and a not in seen:
            ins = next(md.disasm(read(a, 4), a), None)
            if ins is None:
                break
            seen[a] = ins
            mn = ins.mnemonic
            ops = ins.operands
            nxt = ins.address + ins.size

            # Sprungziele einsammeln
            targets = [o.imm for o in ops if o.type == capstone.arm.ARM_OP_IMM]
            is_call = mn in ("bl", "blx")

            # schreibt die Instruktion das PC-Register?
            writes_pc = False
            if ops:
                o0 = ops[0]
                if o0.type == capstone.arm.ARM_OP_REG and ins.reg_name(o0.reg) == "pc":
                    writes_pc = True
            if mn in ("pop", "ldm", "ldmia", "ldmfd", "ldmdb") and "pc" in ins.op_str:
                writes_pc = True

            if mn.startswith("b") and mn not in ("bic", "bfi", "bfc", "bkx"):
                if targets:
                    work.append(targets[0])
                a = nxt
                if mn == "b":
                    break
                continue
            if mn in ("cbz", "cbnz"):
                if targets:
                    work.append(targets[0])
                a = nxt
                continue
            if is_call:
                if targets and start <= targets[0] < stop:
                    work.append(targets[0])
                a = nxt
                continue
            if mn in TERMINATORS or writes_pc:
                break
            a = nxt
    return seen


def main():
    start = int(sys.argv[1], 16)
    stop = int(sys.argv[2], 16) if len(sys.argv) > 2 else start + 0x400
    seen = disasm_cfg(start, stop)
    addr = start
    while addr < stop:
        ins = seen.get(addr)
        if ins is None:
            nxt = min([a for a in seen if a > addr], default=stop)
            print(f"  ; ---- Daten {addr:#08x}..{nxt:#08x} ({nxt - addr} B) ----")
            addr = nxt
            continue
        print(f"  {ins.address:08x}:  {ins.bytes.hex():<10} {ins.mnemonic:<8} {ins.op_str}")
        addr = ins.address + ins.size


if __name__ == "__main__":
    main()

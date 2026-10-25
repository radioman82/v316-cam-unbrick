"""Run one or more shell commands on the camera over COM11.

usage: python sh.py "cmd1" "cmd2" ...
       python sh.py --wait 3 "cmd"
"""
import serial, time, sys

args = sys.argv[1:]
wait = 1.2
if args and args[0] == "--wait":
    wait = float(args[1])
    args = args[2:]

s = serial.Serial("COM11", 115200, timeout=3)


def run(cmd, w=None):
    s.reset_input_buffer()
    s.write(cmd.encode() + b"\n")
    time.sleep(w if w is not None else wait)
    out = b""
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.08)
    return out.decode("utf-8", errors="replace")


for c in args:
    print(f"$ {c}")
    print(run(c))
s.close()

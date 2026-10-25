import serial, time

s = serial.Serial("COM11", 115200, timeout=3)

def run(cmd, wait=1.5):
    s.reset_input_buffer()
    s.write(cmd.encode() + b"\n")
    time.sleep(wait)
    out = b""
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.1)
    return out.decode("utf-8", errors="replace")

run("killall -9 sdvcam 2>/dev/null", 1.0)
run("rm -f /tmp/BOOTHOOK /tmp/crash2.log", 0.5)
run("/usr/bin/sdvcam > /tmp/crash2.log 2>&1 &", 0.8)
time.sleep(14)

print(run("grep -e PC: -e SIGSEGV -e SIGABRT -e stack /tmp/crash2.log | tail -12", 2.0))
print("BOOTHOOK:", run("ls -la /tmp/BOOTHOOK 2>&1", 1.0))
print("ps:", run("ps | grep sdvcam | grep -v grep", 1.0))
s.close()

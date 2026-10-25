import serial, time
s = serial.Serial("COM11", 115200, timeout=3)

def run(cmd, wait=1.2):
    s.reset_input_buffer()
    s.write(cmd.encode() + b"\n")
    time.sleep(wait)
    out = b""
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.1)
    return out.decode("utf-8", errors="replace")

print(run("md5sum /mnt/extsd/sdvcam /mnt/extsd/sdvcam_v8_bak", 1.5))
print(run("ps | grep sdvcam | grep -v grep", 1.0))
print(run("ls -la /mnt/extsd/ | head -12", 1.2))
s.close()

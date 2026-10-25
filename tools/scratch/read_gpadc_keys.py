import serial, time, struct

s = serial.Serial('COM11', 115200, timeout=1)

def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.3)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

print("--- GPADC KEYS CONFIGURATION ---")
cmd = "cd /sys/firmware/devicetree/base/soc@03000000/gpadc && hexdump -C key_cnt && for i in 0 1 2 3 4; do echo \"Key $i:\"; hexdump -C key${i}_vol; hexdump -C key${i}_val; done"
print(run(cmd))
s.close()

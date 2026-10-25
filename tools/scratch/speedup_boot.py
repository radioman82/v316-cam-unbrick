import serial, time

s = serial.Serial('COM11', 115200, timeout=1)

# 1. Optimize S40network (no waiting for DHCP on nonexistent eth0)
s.write(b'echo "#!/bin/sh" > /etc/init.d/S40network\n')
time.sleep(0.1)
s.write(b'echo "exit 0" >> /etc/init.d/S40network\n')
time.sleep(0.1)
s.write(b'chmod 755 /etc/init.d/S40network\n')
time.sleep(0.1)

# 2. Optimize S10udev (remove 30s settle delay)
s.write(b'sed -i "s/--timeout=30/--timeout=1 \&/g" /etc/init.d/S10udev\n')
time.sleep(0.1)

s.write(b'sync\n')
time.sleep(0.2)

s.write(b'cat /etc/init.d/S40network; grep settle /etc/init.d/S10udev\n')
time.sleep(0.4)
out = s.read(s.in_waiting or 1000).decode('utf-8', errors='ignore')
print(out)
s.close()

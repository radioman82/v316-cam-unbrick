import serial, time

s = serial.Serial('COM11', 115200, timeout=1)

with open('d:/v316cm/start_streaming.sh', 'rb') as f:
    content = f.read()

s.write(b'> /mnt/extsd/start_streaming.sh\n')
time.sleep(0.1)

# Write line by line
for line in content.splitlines():
    cmd = f"echo '{line.decode('utf-8')}' >> /mnt/extsd/start_streaming.sh\n"
    s.write(cmd.encode('utf-8'))
    time.sleep(0.03)

s.write(b'chmod +x /mnt/extsd/start_streaming.sh; sync\n')
time.sleep(0.2)
s.write(b'wc -l /mnt/extsd/start_streaming.sh\n')
time.sleep(0.3)
out = s.read(s.in_waiting or 1000).decode('utf-8', errors='ignore')
print(out)
s.close()

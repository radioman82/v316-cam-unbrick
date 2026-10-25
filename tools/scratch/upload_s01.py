import base64, serial, time

with open('d:/v316cm/S01app_clean', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

s = serial.Serial('COM11', 115200, timeout=2)
def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.15)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

print("Clearing /tmp/s01.b64...")
run('rm -f /tmp/s01.b64')

chunk_size = 120
for i in range(0, len(b64), chunk_size):
    chunk = b64[i:i+chunk_size]
    run('echo -n "' + chunk + '" >> /tmp/s01.b64')

print("Decoding /tmp/s01.b64...")
run('base64 -d /tmp/s01.b64 > /etc/init.d/S01app')
run('chmod 755 /etc/init.d/S01app')
run('sync')

print("Verifying /etc/init.d/S01app:")
print(run('ls -l /etc/init.d/S01app'))
print(run('sed -n "60,76p" /etc/init.d/S01app'))
s.close()

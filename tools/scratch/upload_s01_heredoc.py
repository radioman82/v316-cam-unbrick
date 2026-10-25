import serial, time

with open('d:/v316cm/S01app_clean', 'r') as f:
    content = f.read()

s = serial.Serial('COM11', 115200, timeout=2)

def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.1)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.02)
    return out.decode('utf-8', errors='replace')

print("Sending S01app via heredoc...")
s.write(b"cat << 'EOF_S01' > /etc/init.d/S01app\n")
time.sleep(0.2)

for line in content.splitlines():
    s.write(line.encode() + b'\n')
    time.sleep(0.02)

time.sleep(0.2)
s.write(b"EOF_S01\n")
time.sleep(0.5)

run("chmod 755 /etc/init.d/S01app")
run("sync")

print("Verification:")
print(run("ls -l /etc/init.d/S01app"))
print(run("sed -n '60,76p' /etc/init.d/S01app"))
s.close()

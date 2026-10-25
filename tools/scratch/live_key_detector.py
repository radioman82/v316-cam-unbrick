
import serial, time

ser = serial.Serial("COM11", 115200, timeout=0.1)

# Monitor /dev/input/event0, 1, 2 using hexdump
ser.write(b"hexdump /dev/input/event0 &
")
ser.write(b"hexdump /dev/input/event1 &
")
ser.write(b"hexdump /dev/input/event2 &
")

print("Monitoring input events for 10 seconds... Please press buttons now!")
start = time.time()
while time.time() - start < 10:
    chunk = ser.read_all()
    if chunk:
        print(chunk.decode("utf-8", errors="ignore"), end="", flush=True)
    time.sleep(0.05)

ser.write(b"killall hexdump 2>/dev/null\n")
time.sleep(0.5)
ser.close()

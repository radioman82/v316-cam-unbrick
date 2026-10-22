import serial
import time
import sys

def main():
    ser = serial.Serial('COM11', 115200, timeout=0.1)
    print("Listening on COM11 (115200 baud)... Press Ctrl+C or kill to stop.", flush=True)
    with open('live_uart.log', 'a', encoding='utf-8') as f:
        while True:
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                try:
                    text = data.decode('utf-8', errors='replace')
                except Exception:
                    text = repr(data)
                sys.stdout.write(text)
                sys.stdout.flush()
                f.write(text)
                f.flush()
            time.sleep(0.05)

if __name__ == '__main__':
    main()

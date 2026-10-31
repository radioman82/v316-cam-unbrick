"""Framed UART commands and checked base64 reads; no bulk TTY heredocs."""
import base64
import gzip
import re
import time
import uuid
import serial

class CameraUART:
    def __init__(self):
        self.port = serial.Serial('COM11', 115200, timeout=.2, write_timeout=5)
        self.port.write(b'\n')
        time.sleep(.3)
        self.port.reset_input_buffer()
        self.run('stty -echo')
        self.busybox=self.run('if [ -x /opt/cam/bin/busybox ]; then echo /opt/cam/bin/busybox; else echo /mnt/extsd/bin/busybox; fi')

    def run(self, command, timeout=60):
        marker = ('RC_' + uuid.uuid4().hex).encode()
        self.port.write(command.encode() + b"; r=$?; printf '\\n" + marker + b":%s\\n' \"$r\"\n")
        buf = bytearray()
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            buf.extend(self.port.read(self.port.in_waiting or 1))
            match = re.search(rb'\r*\n' + marker + rb':(\d+)\r*\n', buf)
            if match:
                body = bytes(buf[:match.start()]).decode('ascii', errors='replace').replace('\r', '')
                body = body.strip().removeprefix('/ # ').strip()
                if match[1] != b'0':
                    raise RuntimeError(body)
                return body
        raise TimeoutError(command[:100])

    def read(self, path, timeout=60):
        data = self.run(f'gzip -c {path} | {self.busybox} base64', timeout)
        return gzip.decompress(base64.b64decode(data))

    def close(self):
        self.port.write(b'stty echo\n')
        self.port.close()

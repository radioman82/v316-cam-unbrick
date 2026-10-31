"""Deploy via the camera's existing cmd CGI, with backup and a live video probe."""
import argparse
import base64
from datetime import datetime
import hashlib
from pathlib import Path
import shlex
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent


class Camera:
    def __init__(self, base, busybox='/mnt/extsd/bin/busybox'):
        self.base = base.rstrip("/")
        self.busybox = busybox

    def run(self, command):
        if "\n" in command:
            raise ValueError("cmd CGI accepts one shell line")
        marker = "V316CM_RC_" + uuid.uuid4().hex
        line = f"( {command} ); r=$?; printf '\\n{marker}%s\\n' \"$r\""
        req = urllib.request.Request(self.base + "/cgi-bin/cmd", data=(line + "\n").encode())
        with urllib.request.urlopen(req, timeout=20) as response:
            output = response.read().decode(errors="replace")
        body, sep, tail = output.rpartition(marker)
        if not sep or tail.strip() != "0":
            raise RuntimeError(f"Camera command failed: {body}{sep}{tail}")
        return body.strip()

    def upload(self, data, destination):
        path = shlex.quote(destination)
        self.run(f": > {path}")
        for start in range(0, len(data), 4096):
            chunk = base64.b64encode(data[start:start + 4096]).decode()
            self.run(f"printf %s {shlex.quote(chunk)} | {shlex.quote(self.busybox)} base64 -d >> {path}")
        expected = hashlib.md5(data).hexdigest()
        actual = self.run(f"md5sum {path}").split()[0]
        if actual != expected:
            raise RuntimeError(f"Upload checksum mismatch: {destination}")


def read_frames(url, count=8):
    """Check actual multipart framing and independently decodable, changing JPEGs."""
    from PIL import Image
    import io
    import time
    with urllib.request.urlopen(url, timeout=12) as response:
        content_type = response.headers.get("Content-Type", "")
        if "multipart/x-mixed-replace; boundary=v316cmframe" != content_type:
            raise RuntimeError(f"Unexpected Content-Type: {content_type}")
        frames = []
        start = time.monotonic()
        for _ in range(count):
            boundary = response.readline()
            if boundary != b"--v316cmframe\r\n":
                raise RuntimeError(f"Invalid multipart boundary: {boundary!r}")
            headers = {}
            while True:
                line = response.readline()
                if line == b"\r\n":
                    break
                if not line:
                    raise RuntimeError("Stream ended inside frame headers")
                name, value = line.decode().split(":", 1)
                headers[name.lower()] = value.strip()
            length = int(headers["content-length"])
            if headers["content-type"] != "image/jpeg" or not 0 < length < 2_000_000:
                raise RuntimeError("Invalid JPEG frame headers")
            data = response.read(length)
            if len(data) != length or response.read(2) != b"\r\n":
                raise RuntimeError("Truncated JPEG frame")
            with Image.open(io.BytesIO(data)) as image:
                image.load()
                dimensions = image.size
            frames.append(hashlib.sha256(data).hexdigest())
        elapsed = time.monotonic() - start
        unique = len(set(frames))
        if unique < 2:
            raise RuntimeError("Capture is frozen: all JPEG frames are identical")
        print(f"{count} JPEG frames, {unique} different, {dimensions}, "
              f"{(count - 1) / elapsed:.1f} FPS, last frame {length} bytes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://192.168.178.199:8080")
    parser.add_argument("--check", action="store_true", help="Only validate existing stream")
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument("--streaming-only", action="store_true",
                        help="Publish only the player and stream CGI; keep camera controls and startup unchanged")
    args = parser.parse_args()
    if args.frames < 2:
        parser.error("--frames must be at least 2")
    if args.check:
        read_frames(args.url.rstrip("/") + "/cgi-bin/stream", args.frames)
        return
    camera = Camera(args.url)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    backup = "/mnt/extsd/.stream-backup-" + stamp
    stage = "/mnt/extsd/.stream-stage-" + stamp
    camera.run(f"mkdir -p {backup}/cgi-bin {backup}/bin {stage}")
    for name in ("index.html", "cgi-bin/stream", "cgi-bin/snapshot"):
        camera.run(f"cp /mnt/extsd/www/{name} {backup}/{name}")
    camera.run(f"if [ -f /mnt/extsd/www/cgi-bin/control ]; then cp /mnt/extsd/www/cgi-bin/control {backup}/cgi-bin/control; fi")
    camera.run(f"cp /mnt/extsd/start_streaming.sh {backup}/start_streaming.sh")
    camera.run(f"if [ -f /mnt/extsd/bin/v316cm-mjpeg ]; then cp /mnt/extsd/bin/v316cm-mjpeg {backup}/bin/v316cm-mjpeg; fi")
    camera.run(f"if [ -f /mnt/extsd/bin/v316cm-control ]; then cp /mnt/extsd/bin/v316cm-control {backup}/bin/v316cm-control; fi")
    print("Backup:", backup, flush=True)
    files = {
        "v316cm-mjpeg": HERE.parents[1] / "firmware" / "streaming" / "v316cm-mjpeg",
        "v316cm-control": HERE.parents[1] / "firmware" / "streaming" / "v316cm-control",
        "index.html": HERE / "www" / "index.html",
        "stream": HERE / "www" / "cgi-bin" / "stream",
        "snapshot": HERE / "www" / "cgi-bin" / "snapshot",
        "control": HERE / "www" / "cgi-bin" / "control",
        "start_streaming.sh": HERE / "start_streaming.sh",
    }
    if args.streaming_only:
        for name in ("v316cm-control", "control", "start_streaming.sh"):
            del files[name]
    for name, local in files.items():
        camera.upload(local.read_bytes(), stage + "/" + name)
    camera.run(f"chmod 755 {stage}/v316cm-mjpeg")
    probe_name = "v316cm-probe-" + stamp
    probe = "/mnt/extsd/www/cgi-bin/" + probe_name
    camera.upload(f"#!/bin/sh\nexec {stage}/v316cm-mjpeg\n".encode(), probe)
    camera.run(f"chmod 755 {probe}")
    try:
        read_frames(camera.base + "/cgi-bin/" + probe_name)
    finally:
        camera.run(f"rm -f {probe}")
    # Each same-filesystem rename is atomic; publish the page last.
    try:
        camera.run(f"mv {stage}/v316cm-mjpeg /mnt/extsd/bin/v316cm-mjpeg")
        if not args.streaming_only:
            camera.run(f"chmod 755 {stage}/v316cm-control && mv {stage}/v316cm-control /mnt/extsd/bin/v316cm-control")
        for name in (("stream", "snapshot") if args.streaming_only else ("stream", "snapshot", "control")):
            camera.run(f"chmod 755 {stage}/{name} && mv {stage}/{name} /mnt/extsd/www/cgi-bin/{name}")
        if not args.streaming_only:
            camera.run(f"chmod 755 {stage}/start_streaming.sh && mv {stage}/start_streaming.sh /mnt/extsd/start_streaming.sh")
        camera.run(f"mv {stage}/index.html /mnt/extsd/www/index.html && sync")
        read_frames(camera.base + "/cgi-bin/stream", args.frames)
    except Exception:
        for name in ("index.html", "cgi-bin/stream", "cgi-bin/snapshot"):
            camera.run(f"cp {backup}/{name} /mnt/extsd/www/{name}")
        camera.run(f"if [ -f {backup}/bin/v316cm-mjpeg ]; then cp {backup}/bin/v316cm-mjpeg /mnt/extsd/bin/v316cm-mjpeg; fi; sync")
        camera.run(f"cp {backup}/start_streaming.sh /mnt/extsd/start_streaming.sh; if [ -f {backup}/cgi-bin/control ]; then cp {backup}/cgi-bin/control /mnt/extsd/www/cgi-bin/control; fi")
        raise
    camera.run(f"rmdir {stage}")
    print("Live:", camera.base)


if __name__ == "__main__":
    main()

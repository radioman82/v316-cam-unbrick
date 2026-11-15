"""Apply explicit gain with a lookahead peak limiter; never overwrite the source."""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import wave

import imageio_ffmpeg


def stats(path):
    with wave.open(str(path), 'rb') as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 44100)
        params = w.getparams()
        samples = array.array('h', w.readframes(w.getnframes()))
    rms = math.sqrt(sum(x*x for x in samples) / len(samples))
    return {'frames': params.nframes, 'peak': max(abs(x) for x in samples), 'rms_dbfs': 20*math.log10(rms/32768), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--gain', type=float, default=2.0)
    args = p.parse_args()
    assert args.gain > 0 and not args.output.exists()
    before = stats(args.source)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    filters = f'volume={args.gain},alimiter=limit=0.98:attack=5:release=50:level=false:latency=true'
    subprocess.run([ffmpeg, '-nostdin', '-n', '-v', 'error', '-i', str(args.source), '-af', filters, '-ac', '1', '-ar', '44100', '-c:a', 'pcm_s16le', '-map_metadata', '-1', str(args.output)], check=True)
    after = stats(args.output)
    assert before['frames'] == after['frames']
    assert after['peak'] <= 32114
    assert after['rms_dbfs'] > before['rms_dbfs']
    assert stats(args.source) == before
    report = {'gain_before_limiter': args.gain, 'filters': filters, 'before': before, 'after': after, 'rms_increase_db': after['rms_dbfs']-before['rms_dbfs']}
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

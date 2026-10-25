"""Build the v1.0 release package for the Allwinner V316 Cam 4-tile firmware."""
import os, shutil, hashlib, zipfile

HERE = r"d:\v316cm"
REL = os.path.join(HERE, "RELEASE_v1.0_4Kacheln_2026-10-23")
ZIP = os.path.join(HERE, "V316CM_4tiles_v1.0_STABLE_2026-10-23.zip")

os.makedirs(REL, exist_ok=True)

COPY = [
    ("sdvcam_4tiles_final",                      "sdvcam_4tiles_v1.0.bin"),
    ("sdvcam_v8",                                "sdvcam_v8_rollback.bin"),
    ("build_sdvcam_4tiles_final.py",             "build_sdvcam_4tiles_final.py"),
    ("show_stub_final.s",                        "show_stub_final.s"),
    ("apply_build.py",                           "apply_build.py"),
    ("grab_screen.py",                           "grab_screen.py"),
    ("check_state.py",                           "check_state.py"),
    ("ZUSAMMENFASSUNG_V316CM_4Kacheln_2026-10-23.md",
     "ZUSAMMENFASSUNG_V316CM_4Kacheln_2026-10-23.md"),
]

for src, dst in COPY:
    s = os.path.join(HERE, src)
    if not os.path.exists(s):
        raise SystemExit(f"missing: {s}")
    shutil.copy2(s, os.path.join(REL, dst))
    print(f"  {src:55s} -> {dst}")

# checksums
def digests(path):
    d = open(path, "rb").read()
    return hashlib.md5(d).hexdigest(), hashlib.sha256(d).hexdigest()

lines = ["# Allwinner V316 Cam 4-Kachel-Firmware v1.0 — Prüfsummen", ""]
for name in ("sdvcam_4tiles_v1.0.bin", "sdvcam_v8_rollback.bin"):
    p = os.path.join(REL, name)
    md5, sha = digests(p)
    size = os.path.getsize(p)
    lines.append(f"{name}")
    lines.append(f"  size   {size}")
    lines.append(f"  MD5    {md5}")
    lines.append(f"  SHA256 {sha}")
    lines.append("")
open(os.path.join(REL, "CHECKSUMS.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("\nCHECKSUMS.txt:")
print("\n".join(lines))

# zip
if os.path.exists(ZIP):
    os.remove(ZIP)
with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in sorted(os.listdir(REL)):
        fp = os.path.join(REL, f)
        if os.path.isfile(fp):
            z.write(fp, arcname=os.path.join("V316CM_4tiles_v1.0", f))
print(f"\nZIP: {ZIP}")
print(f"     {os.path.getsize(ZIP)} bytes")

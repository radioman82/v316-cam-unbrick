import re

orig_p = r"d:\v316cm\Firmware\firm\versuch6\_full_img_verbose.fex.extracted\squashfs-root\usr\share\minigui\res\lang\zh-DE.xml"
with open(orig_p, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Fix broken umlauts and english placeholders in German XML
replacements = {
    '<string name="function_mode">Mode</string>': '<string name="function_mode">Modus</string>',
    '<string name="function_media">Media</string>': '<string name="function_media">Album</string>',
    '<string name="function_setting">Setting</string>': '<string name="function_setting">Setup</string>',
    '<string name="function_return">Return</string>': '<string name="function_return">Zurück</string>',
    '<string name="mode_normal_rec">Video</string>': '<string name="mode_normal_rec">Video</string>',
    '<string name="mode_normal_pic">Photo</string>': '<string name="mode_normal_pic">Foto</string>',
    '<string name="mode_timelapse_rec">Lapse</string>': '<string name="mode_timelapse_rec">Zeitraffer</string>',
    '<string name="mode_loop_rec">Loop</string>': '<string name="mode_loop_rec">Endlos</string>',
    '<string name="mode_slowly_rec">Slowly</string>': '<string name="mode_slowly_rec">Zeitlupe</string>',
    '<string name="mode_continue_pic">Burst</string>': '<string name="mode_continue_pic">Serie</string>',
    '<string name="mode_timing_pic">Timer</string>': '<string name="mode_timing_pic">Timer</string>',
    '<string name="mode_auto_pic">Auto</string>': '<string name="mode_auto_pic">Auto</string>',
    'Videoauflsung': 'Video-Auflösung',
    'Videocodierungstyp': 'Video-Codec',
    'Video Ton': 'Tonaufnahme',
    'Anti-Shake': 'Stabilisator',
    'SD-Karte formatieren?': 'Karte formatieren?',
    'Format': 'Formatieren',
    'Cancel': 'Abbrechen',
}

for old, new in replacements.items():
    content = content.replace(old, new)

out_p = r"d:\v316cm\zh-DE_clean.xml"
with open(out_p, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Cleaned German XML written to {out_p}")

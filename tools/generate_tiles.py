import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = r"d:\v316cm\custom_ui"
os.makedirs(OUT_DIR, exist_ok=True)

FONT_PATH = r"C:\Windows\Fonts\segoeuib.ttf"

def create_tile(width, height, title_lines, subtitle=None, accent_color=(0, 210, 255), is_hi=False):
    # Base background: deep dark slate
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Margin and card bounds
    m = 2
    x0, y0, x1, y1 = m, m, width - 1 - m, height - 1 - m
    r = 10  # corner radius
    
    # Background fill
    if is_hi:
        fill_color = (accent_color[0] // 3, accent_color[1] // 3, accent_color[2] // 3, 240)
        border_color = accent_color
        border_w = 3
    else:
        fill_color = (20, 25, 34, 235)
        border_color = (60, 75, 95, 200)
        border_w = 2

    # Draw rounded card
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill_color, outline=border_color, width=border_w)
    
    # Top accent bar/glow
    accent_bar_h = 4
    if is_hi:
        draw.rounded_rectangle([x0 + 4, y0 + 3, x1 - 4, y0 + 3 + accent_bar_h], radius=2, fill=accent_color)
    else:
        draw.rounded_rectangle([x0 + 6, y0 + 3, x1 - 6, y0 + 3 + 2], radius=1, fill=(accent_color[0], accent_color[1], accent_color[2], 180))

    # Calculate font sizes
    # If 1 line or 2 lines
    n_lines = len(title_lines)
    if height > 100:
        # 159x119 tile
        font_size = 22 if n_lines == 1 else 17
    else:
        # 80x90 tile
        font_size = 14 if n_lines == 1 else 12

    font = ImageFont.truetype(FONT_PATH, font_size)
    
    # Measure text height
    line_heights = []
    line_widths = []
    for l in title_lines:
        bbox = draw.textbbox((0, 0), l, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        line_widths.append(w)
        line_heights.append(h)
    
    total_h = sum(line_heights) + (n_lines - 1) * 4
    start_y = (height - total_h) // 2 + 3
    
    # Draw text lines centered
    curr_y = start_y
    for i, l in enumerate(title_lines):
        w = line_widths[i]
        curr_x = (width - w) // 2
        text_color = (255, 255, 255, 255) if not is_hi else (255, 255, 255, 255)
        # Drop shadow
        draw.text((curr_x + 1, curr_y + 1), l, font=font, fill=(0, 0, 0, 200))
        draw.text((curr_x, curr_y), l, font=font, fill=text_color)
        curr_y += line_heights[i] + 4

    return img

print("Generating Function Tiles (159x119)...")
func_tiles = [
    ("function_mode.png", ["MODUS"], (255, 82, 82)),      # Vibrant Red/Coral
    ("function_media.png", ["ALBUM"], (0, 210, 255)),     # Cyan
    ("function_setting.png", ["SETUP"], (255, 179, 0)),   # Amber/Gold
    ("function_return.png", ["ZURÜCK"], (105, 240, 174)), # Emerald Green
]

for name, lines, col in func_tiles:
    im = create_tile(159, 119, lines, accent_color=col, is_hi=False)
    p = os.path.join(OUT_DIR, name)
    im.save(p, "PNG")
    print(f"  Created {name}")

print("\nGenerating Mode Tiles (80x90)...")
mode_tiles = [
    ("mode_normal_rec", ["VIDEO"], (255, 82, 82)),
    ("mode_normal_pic", ["FOTO"], (0, 210, 255)),
    ("mode_timelapse_rec", ["ZEIT-", "RAFFER"], (179, 136, 255)),
    ("mode_loop_rec", ["LOOP"], (255, 215, 64)),
    ("mode_slowly_rec", ["ZEIT-", "LUPE"], (77, 208, 225)),
    ("mode_continue_pic", ["SERIE"], (255, 138, 101)),
    ("mode_timing_pic", ["TIMER"], (200, 230, 201)),
    ("mode_auto_pic", ["AUTO"], (244, 143, 177)),
]

for base_name, lines, col in mode_tiles:
    # Normal state
    im_norm = create_tile(80, 90, lines, accent_color=col, is_hi=False)
    p_norm = os.path.join(OUT_DIR, f"{base_name}.png")
    im_norm.save(p_norm, "PNG")
    
    # Highlighted state (RGB or RGBA)
    im_hi = create_tile(80, 90, lines, accent_color=col, is_hi=True)
    p_hi = os.path.join(OUT_DIR, f"{base_name}_hi.png")
    im_hi.save(p_hi, "PNG")
    print(f"  Created {base_name}.png and _hi.png")

print(f"\nAll tiles successfully written to {OUT_DIR}")

import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = r"d:\v316cm\custom_ui"
os.makedirs(OUT_DIR, exist_ok=True)

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"

def create_tile(width, height, title, subtitle, accent_color, icon_type):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer margin and card geometry
    m = 2
    x0, y0, x1, y1 = m, m, width - 1 - m, height - 1 - m
    r = 10
    
    # Dark modern card background with subtle gradient/accent tint
    bg_fill = (18, 22, 30, 245)
    border_color = (accent_color[0] // 2, accent_color[1] // 2, accent_color[2] // 2, 220)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=bg_fill, outline=border_color, width=2)
    
    # Accent top indicator bar
    draw.rounded_rectangle([x0 + 8, y0 + 4, x1 - 8, y0 + 8], radius=2, fill=accent_color)
    
    # Icon drawing in center
    cx = width // 2
    cy = 44
    
    if icon_type == "camera": # FOTO
        # Camera body
        draw.rounded_rectangle([cx - 20, cy - 12, cx + 20, cy + 14], radius=4, fill=(40, 50, 68, 255), outline=accent_color, width=2)
        # Top bump
        draw.rectangle([cx - 8, cy - 16, cx + 4, cy - 12], fill=accent_color)
        # Lens
        draw.ellipse([cx - 9, cy - 7, cx + 9, cy + 9], fill=(20, 25, 35, 255), outline=accent_color, width=2)
        draw.ellipse([cx - 4, cy - 2, cx + 4, cy + 4], fill=accent_color)
        
    elif icon_type == "video": # VIDEO
        # Video camera body
        draw.rounded_rectangle([cx - 18, cy - 12, cx + 10, cy + 14], radius=3, fill=(40, 50, 68, 255), outline=accent_color, width=2)
        # Lens cone
        draw.polygon([(cx + 10, cy - 3), (cx + 22, cy - 12), (cx + 22, cy + 14), (cx + 10, cy + 5)], fill=accent_color)
        # REC red circle
        draw.ellipse([cx - 12, cy - 6, cx - 2, cy + 4], fill=(255, 60, 60, 255))
        
    elif icon_type == "stream": # STREAMING (WiFi / Live Broadcast)
        # WiFi arcs
        draw.arc([cx - 20, cy - 18, cx + 20, cy + 22], start=210, end=330, fill=accent_color, width=3)
        draw.arc([cx - 13, cy - 11, cx + 13, cy + 15], start=210, end=330, fill=accent_color, width=3)
        draw.arc([cx - 6, cy - 4, cx + 6, cy + 8], start=210, end=330, fill=accent_color, width=3)
        # Center dot
        draw.ellipse([cx - 2, cy + 8, cx + 2, cy + 12], fill=accent_color)
        
    elif icon_type == "setup": # SETUP (Gear)
        # Outer gear hub
        draw.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=(40, 50, 68, 255), outline=accent_color, width=2)
        # Gear teeth
        for ang in [0, 45, 90, 135, 180, 225, 270, 315]:
            import math
            rad = math.radians(ang)
            gx = cx + int(16 * math.cos(rad))
            gy = cy + int(16 * math.sin(rad))
            draw.ellipse([gx - 3, gy - 3, gx + 3, gy + 3], fill=accent_color)
        # Inner hole
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(18, 22, 30, 255), outline=accent_color, width=2)

    # Typography
    f_title = ImageFont.truetype(FONT_BOLD, 20)
    f_sub = ImageFont.truetype(FONT_REG, 13)
    
    # Title bbox
    t_bbox = draw.textbbox((0, 0), title, font=f_title)
    t_w = t_bbox[2] - t_bbox[0]
    t_x = (width - t_w) // 2
    t_y = 68
    
    # Subtitle bbox
    s_bbox = draw.textbbox((0, 0), subtitle, font=f_sub)
    s_w = s_bbox[2] - s_bbox[0]
    s_x = (width - s_w) // 2
    s_y = 92
    
    # Shadow and Title text
    draw.text((t_x + 1, t_y + 1), title, font=f_title, fill=(0, 0, 0, 220))
    draw.text((t_x, t_y), title, font=f_title, fill=(255, 255, 255, 255))
    
    # Subtitle text
    draw.text((s_x, s_y), subtitle, font=f_sub, fill=(180, 195, 215, 240))
    
    return img

tiles = [
    ("function_mode.png", "1. FOTO", "Foto-Modus", (0, 210, 255), "camera"),       # Cyan
    ("function_media.png", "2. VIDEO", "Video-Modus", (255, 75, 75), "video"),     # Coral Red
    ("function_setting.png", "3. STREAM", "WLAN Kamera", (46, 213, 115), "stream"), # Emerald Green
    ("function_return.png", "4. SETUP", "Einstellungen", (255, 180, 50), "setup"),  # Amber Gold
]

for filename, title, sub, col, icon in tiles:
    im = create_tile(159, 119, title, sub, col, icon)
    p = os.path.join(OUT_DIR, filename)
    im.save(p, "PNG")
    print(f"Generated {filename} -> {title} ({col})")

print("All 4 tiles successfully generated in", OUT_DIR)

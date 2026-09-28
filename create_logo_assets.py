import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from apps.core.models import SchoolSetting
from PIL import Image, ImageDraw, ImageFont

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 600" width="500" height="600">
  <defs>
    <!-- Outer Shield Clip -->
    <clipPath id="shield-clip">
      <path d="M 250,20 L 440,75 C 440,280 370,440 250,510 C 130,440 60,280 60,75 Z" />
    </clipPath>
    <!-- Inner Shield Clip -->
    <clipPath id="inner-shield-clip">
      <path d="M 250,36 L 424,86 C 424,272 360,422 250,490 C 140,422 76,272 76,86 Z" />
    </clipPath>
    <linearGradient id="red-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#cf232a"/>
      <stop offset="100%" stop-color="#b01b22"/>
    </linearGradient>
    <linearGradient id="blue-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0e345e"/>
      <stop offset="100%" stop-color="#0a2544"/>
    </linearGradient>
    <linearGradient id="globe-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#00a8e8"/>
      <stop offset="100%" stop-color="#0077b6"/>
    </linearGradient>
  </defs>

  <!-- Outer Dark Shield Frame -->
  <path d="M 250,14 L 448,70 C 448,288 375,452 250,526 C 125,452 52,288 52,70 Z" fill="#0b1726" stroke="#1e293b" stroke-width="3"/>
  
  <!-- White Shield Border -->
  <path d="M 250,24 L 436,78 C 436,280 366,436 250,504 C 134,436 64,280 64,78 Z" fill="#ffffff"/>

  <!-- Main Shield Body with Inner Clip -->
  <g clip-path="url(#inner-shield-clip)">
    <!-- Top Red Background -->
    <rect x="0" y="0" width="500" height="260" fill="url(#red-grad)" />

    <!-- Globe & Education Graphics -->
    <g transform="translate(250, 150)">
      <!-- Globe Circle -->
      <circle cx="0" cy="-10" r="42" fill="url(#globe-grad)" stroke="#ffffff" stroke-width="2.5"/>
      <!-- Globe Continents -->
      <path d="M -24,-20 Q -10,-32 8,-28 Q 24,-24 18,-6 Q 8,-12 -8,-4 Q -22,-6 -24,-20 Z" fill="#f8fafc" opacity="0.95"/>
      <path d="M -30,5 Q -18,-2 -6,8 Q 2,24 -14,28 Q -28,26 -30,5 Z" fill="#f8fafc" opacity="0.95"/>
      <path d="M 8,4 Q 24,-2 32,8 Q 28,22 14,24 Q 4,16 8,4 Z" fill="#f8fafc" opacity="0.95"/>

      <!-- Graduation Cap / Mortarboard -->
      <!-- Cap Diamond -->
      <polygon points="0,-48 48,-32 0,-16 -48,-32" fill="#0f172a" stroke="#1e293b" stroke-width="1.5"/>
      <!-- Cap Skullcap -->
      <path d="M -22,-24 C -22,-12 22,-12 22,-24 Z" fill="#0f172a"/>
      <!-- Cap Tassel -->
      <path d="M 0,-32 Q -38,-28 -38,-6" stroke="#f59e0b" stroke-width="2.5" fill="none"/>
      <circle cx="-38" cy="-4" r="3.5" fill="#f59e0b"/>

      <!-- Open Book Beneath Globe -->
      <!-- Left Page -->
      <path d="M 0,22 Q -42,16 -76,32 C -76,46 -42,32 0,38 Z" fill="#0b1726" stroke="#ffffff" stroke-width="1.5"/>
      <path d="M -8,25 Q -40,21 -68,34" stroke="#ffffff" stroke-width="1.5" fill="none"/>
      <path d="M -8,30 Q -38,26 -64,38" stroke="#ffffff" stroke-width="1.5" fill="none"/>
      <!-- Right Page -->
      <path d="M 0,22 Q 42,16 76,32 C 76,46 42,32 0,38 Z" fill="#0b1726" stroke="#ffffff" stroke-width="1.5"/>
      <path d="M 8,25 Q 40,21 68,34" stroke="#ffffff" stroke-width="1.5" fill="none"/>
      <path d="M 8,30 Q 38,26 64,38" stroke="#ffffff" stroke-width="1.5" fill="none"/>
      <!-- Book Spine -->
      <polygon points="-3,22 3,22 0,39" fill="#f59e0b"/>
    </g>

    <!-- Middle White Banner -->
    <rect x="60" y="252" width="380" height="98" fill="#ffffff" />
    <line x1="70" y1="252" x2="430" y2="252" stroke="#0b1726" stroke-width="3"/>
    <line x1="70" y1="350" x2="430" y2="350" stroke="#0b1726" stroke-width="3"/>

    <!-- School Branding Text -->
    <text x="250" y="300" 
          font-family="system-ui, -apple-system, 'Arial Black', 'Impact', sans-serif" 
          font-size="34" 
          font-weight="900" 
          text-anchor="middle" 
          fill="#0a192f" 
          letter-spacing="0.5">GEN&#39;X VISION</text>
    
    <text x="250" y="335" 
          font-family="system-ui, -apple-system, 'Arial', sans-serif" 
          font-size="19" 
          font-weight="800" 
          text-anchor="middle" 
          fill="#c1272d" 
          letter-spacing="3.5">SCHOOL SYSTEM</text>

    <!-- Bottom Deep Blue Background -->
    <rect x="0" y="350" width="500" height="200" fill="url(#blue-grad)" />

    <!-- Pen Nib / Fountain Pen Tip Graphic -->
    <g transform="translate(250, 420)">
      <!-- Outer Nib Body in White -->
      <path d="M 0,-48 L 26,0 L 18,36 L -18,36 L -26,0 Z" fill="#ffffff" />
      <!-- Inner Slit & Breather Hole -->
      <line x1="0" y1="-46" x2="0" y2="-6" stroke="#0a2544" stroke-width="3.5" stroke-linecap="round"/>
      <circle cx="0" cy="-6" r="4.5" fill="#0a2544"/>
      <!-- Nib Collar Base -->
      <path d="M -14,36 L 14,36 L 10,44 L -10,44 Z" fill="#ffffff"/>
    </g>
  </g>
</svg>
'''

# 1. Save SVG
os.makedirs('static/images', exist_ok=True)
os.makedirs('media/school_branding', exist_ok=True)

with open('static/images/logo.svg', 'w', encoding='utf-8') as f:
    f.write(svg_content)

with open('media/school_branding/logo.svg', 'w', encoding='utf-8') as f:
    f.write(svg_content)

print("[SUCCESS] Saved static/images/logo.svg and media/school_branding/logo.svg")

# 2. Generate High Resolution PNG using PIL
width, height = 600, 720
img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Helper to draw shield
def get_shield_points(scale=1.0, offset_y=0):
    cx = width // 2
    top_w = int(225 * scale)
    mid_y = int(320 * scale) + offset_y
    bot_y = int(580 * scale) + offset_y
    top_y = int(50 * scale) + offset_y
    return [
        (cx, top_y - int(18 * scale)),
        (cx + top_w, top_y + int(45 * scale)),
        (cx + top_w, mid_y),
        (cx, bot_y),
        (cx - top_w, mid_y),
        (cx - top_w, top_y + int(45 * scale))
    ]

# Outer dark border
outer_pts = get_shield_points(1.04, 0)
draw.polygon(outer_pts, fill=(11, 23, 38, 255))

# White middle border
white_pts = get_shield_points(0.98, 3)
draw.polygon(white_pts, fill=(255, 255, 255, 255))

# Inner shield clipping layer
inner_pts = get_shield_points(0.93, 6)
shield_mask = Image.new("L", (width, height), 0)
mask_draw = ImageDraw.Draw(shield_mask)
mask_draw.polygon(inner_pts, fill=255)

# Shield content layer
content = Image.new("RGBA", (width, height), (0, 0, 0, 0))
cdraw = ImageDraw.Draw(content)

# Top Red Field
cdraw.rectangle([0, 0, width, 330], fill=(193, 39, 45, 255))

# Globe & Cap
cx = width // 2
# Globe
cdraw.ellipse([cx - 48, 140, cx + 48, 236], fill=(0, 168, 232, 255), outline=(255, 255, 255, 255), width=3)
cdraw.pieslice([cx - 30, 155, cx + 15, 215], 10, 120, fill=(245, 245, 245, 240))
cdraw.pieslice([cx - 5, 175, cx + 38, 225], 200, 310, fill=(245, 245, 245, 240))

# Cap
cdraw.polygon([(cx, 95), (cx + 58, 115), (cx, 135), (cx - 58, 115)], fill=(15, 23, 42, 255))
cdraw.polygon([(cx - 28, 125), (cx + 28, 125), (cx + 20, 142), (cx - 20, 142)], fill=(15, 23, 42, 255))
# Tassel
cdraw.line([(cx, 115), (cx - 48, 125), (cx - 48, 150)], fill=(245, 158, 11, 255), width=3)
cdraw.ellipse([cx - 52, 148, cx - 44, 156], fill=(245, 158, 11, 255))

# Open Book
cdraw.polygon([(cx, 222), (cx - 85, 235), (cx - 85, 250), (cx, 242)], fill=(11, 23, 38, 255))
cdraw.polygon([(cx, 222), (cx + 85, 235), (cx + 85, 250), (cx, 242)], fill=(11, 23, 38, 255))
cdraw.line([(cx - 75, 240), (cx - 10, 230)], fill=(255, 255, 255, 255), width=2)
cdraw.line([(cx + 10, 230), (cx + 75, 240)], fill=(255, 255, 255, 255), width=2)
cdraw.line([(cx - 70, 245), (cx - 10, 236)], fill=(255, 255, 255, 255), width=2)
cdraw.line([(cx + 10, 236), (cx + 70, 245)], fill=(255, 255, 255, 255), width=2)

# Middle White Banner
cdraw.rectangle([0, 330, width, 445], fill=(255, 255, 255, 255))
cdraw.line([0, 330, width, 330], fill=(11, 23, 38, 255), width=4)
cdraw.line([0, 445, width, 445], fill=(11, 23, 38, 255), width=4)

# Text on White Banner
try:
    font_main = ImageFont.truetype("arialbd.ttf", 36)
    font_sub = ImageFont.truetype("arialbd.ttf", 20)
except Exception:
    font_main = ImageFont.load_default()
    font_sub = ImageFont.load_default()

cdraw.text((cx, 382), "GEN'X VISION", fill=(10, 25, 47, 255), font=font_main, anchor="mm")
cdraw.text((cx, 420), "SCHOOL SYSTEM", fill=(193, 39, 45, 255), font=font_sub, anchor="mm")

# Bottom Deep Blue Field
cdraw.rectangle([0, 445, width, height], fill=(14, 52, 94, 255))

# Fountain Pen Nib
nib_y = 525
cdraw.polygon([
    (cx, nib_y - 55),
    (cx + 30, nib_y),
    (cx + 20, nib_y + 40),
    (cx - 20, nib_y + 40),
    (cx - 30, nib_y)
], fill=(255, 255, 255, 255))
cdraw.line([(cx, nib_y - 50), (cx, nib_y - 8)], fill=(14, 52, 94, 255), width=4)
cdraw.ellipse([cx - 5, nib_y - 10, cx + 5, nib_y], fill=(14, 52, 94, 255))
cdraw.polygon([(cx - 15, nib_y + 40), (cx + 15, nib_y + 40), (cx + 12, nib_y + 48), (cx - 12, nib_y + 48)], fill=(255, 255, 255, 255))

# Composite masked content onto base
img.paste(content, (0, 0), shield_mask)

# Save PNGs
img.save("static/images/logo.png", "PNG")
img.save("media/school_branding/logo.png", "PNG")
print("[SUCCESS] Generated static/images/logo.png and media/school_branding/logo.png")

# 3. Update Database SchoolSetting
s = SchoolSetting.get_settings()
s.school_name = "GEN'X VISION SCHOOL SYSTEM"
s.tagline = "Inspiring Excellence, Empowering Future"
s.logo = "school_branding/logo.png"
s.save()
print(f"[SUCCESS] Database SchoolSetting updated to: {s.school_name} (Logo: {s.logo})")

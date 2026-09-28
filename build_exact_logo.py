import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from PIL import Image, ImageDraw, ImageFont

# Pixel-perfect SVG matching user's Image 2 exactly
svg_exact = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 720" width="100%" height="100%">
  <defs>
    <!-- Outer Shield Outline Path -->
    <!-- Top curved upward to center peak, vertical straight sides, angled bottom pointing to center tip -->
    <clipPath id="shield-outer-clip">
      <path d="M 300,35 Q 420,55 530,90 L 530,390 C 530,545 425,640 300,695 C 175,640 70,545 70,390 L 70,90 Q 180,55 300,35 Z" />
    </clipPath>

    <!-- Inner Shield Clip (inset by 18px for the white border) -->
    <clipPath id="shield-inner-clip">
      <path d="M 300,53 Q 412,71 512,102 L 512,388 C 512,530 415,620 300,672 C 185,620 88,530 88,388 L 88,102 Q 188,71 300,53 Z" />
    </clipPath>
  </defs>

  <!-- 1. Thick Outer Black/Navy Shield Shadow & Frame -->
  <path d="M 300,24 Q 425,45 540,82 L 540,394 C 540,556 430,655 300,712 C 170,655 60,556 60,394 L 60,82 Q 175,45 300,24 Z" fill="#0b131f" />

  <!-- 2. Crisp White Shield Border -->
  <path d="M 300,38 Q 418,57 528,92 L 528,390 C 528,542 423,636 300,690 C 177,636 72,542 72,390 L 72,92 Q 182,57 300,38 Z" fill="#ffffff" />

  <!-- 3. Shield Contents (Clipped to Inner Boundary) -->
  <g clip-path="url(#shield-inner-clip)">
    <!-- TOP RED FIELD -->
    <rect x="0" y="0" width="600" height="375" fill="#b91c1c" />

    <!-- EDUCATION EMBLEM GRAPHICS -->
    <g transform="translate(300, 215)">
      <!-- Globe Base Circle -->
      <circle cx="0" cy="-30" r="56" fill="#0284c7" stroke="#ffffff" stroke-width="3.5"/>
      
      <!-- Globe Continents in White with Golden Edge Details -->
      <!-- Continent 1 (North/Eurasia) -->
      <path d="M -34,-48 C -20,-60 6,-56 18,-48 C 30,-40 24,-16 6,-26 C -10,-36 -26,-30 -34,-48 Z" fill="#ffffff"/>
      <path d="M -14,-46 C -2,-52 12,-48 16,-42" stroke="#f59e0b" stroke-width="2" fill="none"/>
      
      <!-- Continent 2 (South America/Africa) -->
      <path d="M -40,-14 C -24,-24 -8,-10 -18,16 C -30,30 -48,16 -40,-14 Z" fill="#ffffff"/>
      <path d="M -32,2 C -24,-10 -12,0 -18,14" stroke="#f59e0b" stroke-width="2" fill="none"/>
      
      <!-- Continent 3 (Asia/Australia) -->
      <path d="M 14,-18 C 34,-26 48,-8 44,16 C 30,26 18,6 14,-18 Z" fill="#ffffff"/>
      <path d="M 22,-8 C 34,-14 42,-2 38,12" stroke="#f59e0b" stroke-width="2" fill="none"/>

      <!-- Graduation Cap / Mortarboard -->
      <!-- Cap Diamond Top -->
      <polygon points="0,-76 72,-54 0,-32 -72,-54" fill="#0f172a" stroke="#000000" stroke-width="1.5"/>
      <!-- Cap Base Skullcap -->
      <path d="M -34,-44 C -34,-24 34,-24 34,-44 Z" fill="#0f172a" stroke="#000000" stroke-width="1"/>
      <!-- Cap Golden Tassel (Left Side) -->
      <circle cx="0" cy="-54" r="4.5" fill="#f59e0b"/>
      <path d="M 0,-54 Q -52,-48 -52,-14" stroke="#f59e0b" stroke-width="4" fill="none"/>
      <polygon points="-52,-14 -47,-2 -57,-2" fill="#f59e0b"/>

      <!-- Open Book Beneath Globe -->
      <!-- Left Book Page -->
      <path d="M 0,22 C -48,10 -94,26 -122,46 C -122,60 -74,38 0,48 Z" fill="#0f172a" stroke="#000000" stroke-width="1.5"/>
      <path d="M -14,28 C -48,20 -88,32 -112,48" stroke="#ffffff" stroke-width="2.5" fill="none"/>
      <path d="M -14,35 C -48,27 -84,39 -104,54" stroke="#ffffff" stroke-width="2.5" fill="none"/>
      
      <!-- Right Book Page -->
      <path d="M 0,22 C 48,10 94,26 122,46 C 122,60 74,38 0,48 Z" fill="#0f172a" stroke="#000000" stroke-width="1.5"/>
      <path d="M 14,28 C 48,20 88,32 112,48" stroke="#ffffff" stroke-width="2.5" fill="none"/>
      <path d="M 14,35 C 48,27 84,39 104,54" stroke="#ffffff" stroke-width="2.5" fill="none"/>
      
      <!-- Center Book Binding Ribbon -->
      <polygon points="-4,22 4,22 0,50" fill="#f59e0b"/>
    </g>

    <!-- MIDDLE WHITE BANNER -->
    <rect x="0" y="370" width="600" height="124" fill="#ffffff" />
    <line x1="0" y1="370" x2="600" y2="370" stroke="#0b131f" stroke-width="4.5"/>
    <line x1="0" y1="494" x2="600" y2="494" stroke="#0b131f" stroke-width="4.5"/>

    <!-- Bold Condensed GEN'X VISION text -->
    <text x="300" y="432" 
          font-family="'Impact', 'Arial Black', 'Trebuchet MS', sans-serif" 
          font-size="48" 
          font-weight="900" 
          text-anchor="middle" 
          fill="#0b131f" 
          letter-spacing="0.5">GEN&#39;X VISION</text>
    
    <!-- Bold Red SCHOOL SYSTEM text -->
    <text x="300" y="474" 
          font-family="'Arial Black', 'Impact', sans-serif" 
          font-size="24" 
          font-weight="900" 
          text-anchor="middle" 
          fill="#b91c1c" 
          letter-spacing="4.5">SCHOOL SYSTEM</text>

    <!-- BOTTOM ROYAL NAVY BLUE SECTION -->
    <rect x="0" y="494" width="600" height="250" fill="#0f3b73" />

    <!-- FOUNTAIN PEN NIB SYMBOL -->
    <g transform="translate(300, 580)">
      <!-- Pen Nib Body Shape (White) -->
      <path d="M 0,-72 L 38,-4 L 26,46 L -26,46 L -38,-4 Z" fill="#ffffff" stroke="#ffffff" stroke-width="1"/>
      
      <!-- Center Slit & Breather Hole (Navy Blue) -->
      <line x1="0" y1="-70" x2="0" y2="-12" stroke="#0f3b73" stroke-width="5" stroke-linecap="round"/>
      <circle cx="0" cy="-12" r="6.5" fill="#0f3b73"/>
      
      <!-- Base Collar Ring (White) -->
      <path d="M -20,46 L 20,46 L 16,56 L -16,56 Z" fill="#ffffff"/>
    </g>
  </g>
</svg>
'''

with open('static/images/logo.svg', 'w', encoding='utf-8') as f:
    f.write(svg_exact)
with open('media/school_branding/logo.svg', 'w', encoding='utf-8') as f:
    f.write(svg_exact)

# 2. Render High-Resolution Raster PNG (1200 x 1440)
W, H = 1200, 1440
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

def get_exact_shield_points(scale=1.0, off_y=0):
    cx = W // 2
    top_w = int(455 * scale)
    mid_y = int(800 * scale) + off_y
    bot_y = int(1370 * scale) + off_y
    top_y = int(105 * scale) + off_y
    return [
        (cx, top_y - int(35 * scale)),
        (cx + top_w, top_y + int(85 * scale)),
        (cx + top_w, mid_y),
        (cx, bot_y),
        (cx - top_w, mid_y),
        (cx - top_w, top_y + int(85 * scale))
    ]

# Outer Black-Navy Shield
draw.polygon(get_exact_shield_points(1.05, 0), fill=(11, 19, 31, 255))
# White Inner Border
draw.polygon(get_exact_shield_points(1.00, 6), fill=(255, 255, 255, 255))

# Mask for interior
mask_layer = Image.new("L", (W, H), 0)
mdraw = ImageDraw.Draw(mask_layer)
mdraw.polygon(get_exact_shield_points(0.95, 12), fill=255)

# Content inside shield
content = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cdraw = ImageDraw.Draw(content)

# 1. Top Red
cdraw.rectangle([0, 0, W, 740], fill=(185, 28, 28, 255))

# Globe & Cap graphics
cx = W // 2
# Globe
cdraw.ellipse([cx - 105, 310, cx + 105, 520], fill=(2, 132, 199, 255), outline=(255, 255, 255, 255), width=6)
cdraw.pieslice([cx - 75, 335, cx + 35, 470], 10, 125, fill=(255, 255, 255, 255))
cdraw.pieslice([cx - 25, 385, cx + 85, 495], 190, 310, fill=(255, 255, 255, 255))

# Mortarboard
cdraw.polygon([(cx, 220), (cx + 130, 265), (cx, 305), (cx - 130, 265)], fill=(15, 23, 42, 255))
cdraw.polygon([(cx - 60, 290), (cx + 60, 290), (cx + 45, 325), (cx - 45, 325)], fill=(15, 23, 42, 255))
# Tassel
cdraw.line([(cx, 265), (cx - 105, 280), (cx - 105, 345)], fill=(245, 158, 11, 255), width=7)
cdraw.ellipse([cx - 114, 340, cx - 96, 358], fill=(245, 158, 11, 255))

# Open Book
cdraw.polygon([(cx, 500), (cx - 180, 530), (cx - 180, 565), (cx, 542)], fill=(15, 23, 42, 255))
cdraw.polygon([(cx, 500), (cx + 180, 530), (cx + 180, 565), (cx, 542)], fill=(15, 23, 42, 255))
cdraw.line([(cx - 155, 538), (cx - 25, 518)], fill=(255, 255, 255, 255), width=5)
cdraw.line([(cx + 25, 518), (cx + 155, 538)], fill=(255, 255, 255, 255), width=5)
cdraw.line([(cx - 145, 552), (cx - 25, 532)], fill=(255, 255, 255, 255), width=5)
cdraw.line([(cx + 25, 532), (cx + 145, 552)], fill=(255, 255, 255, 255), width=5)

# 2. Middle White Banner
cdraw.rectangle([0, 740, W, 988], fill=(255, 255, 255, 255))
cdraw.line([0, 740, W, 740], fill=(11, 19, 31, 255), width=8)
cdraw.line([0, 988, W, 988], fill=(11, 19, 31, 255), width=8)

try:
    font_main = ImageFont.truetype("impact.ttf", 94)
except Exception:
    try:
        font_main = ImageFont.truetype("arialbd.ttf", 80)
    except Exception:
        font_main = ImageFont.load_default()

try:
    font_sub = ImageFont.truetype("arialbd.ttf", 46)
except Exception:
    font_sub = ImageFont.load_default()

cdraw.text((cx, 842), "GEN'X VISION", fill=(11, 19, 31, 255), font=font_main, anchor="mm")
cdraw.text((cx, 930), "SCHOOL SYSTEM", fill=(185, 28, 28, 255), font=font_sub, anchor="mm")

# 3. Bottom Royal Navy Field
cdraw.rectangle([0, 988, W, H], fill=(15, 59, 115, 255))

# Fountain Pen Nib
nib_y = 1170
cdraw.polygon([
    (cx, nib_y - 125),
    (cx + 66, nib_y),
    (cx + 46, nib_y + 88),
    (cx - 46, nib_y + 88),
    (cx - 66, nib_y)
], fill=(255, 255, 255, 255))
cdraw.line([(cx, nib_y - 120), (cx, nib_y - 16)], fill=(15, 59, 115, 255), width=9)
cdraw.ellipse([cx - 12, nib_y - 24, cx + 12, nib_y], fill=(15, 59, 115, 255))
cdraw.polygon([(cx - 36, nib_y + 88), (cx + 36, nib_y + 88), (cx + 28, nib_y + 108), (cx - 28, nib_y + 108)], fill=(255, 255, 255, 255))

# Merge
img.paste(content, (0, 0), mask_layer)
img.save("static/images/logo.png", "PNG")
img.save("media/school_branding/logo.png", "PNG")
print("[SUCCESS] High-resolution authentic emblem generated and saved!")

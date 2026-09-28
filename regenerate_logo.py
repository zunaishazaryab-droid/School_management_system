import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from PIL import Image, ImageDraw, ImageFont

# 1. Generate clean, high-precision SVG matching the exact user emblem
svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 720" width="100%" height="100%">
  <defs>
    <!-- Outer Shield Path -->
    <clipPath id="shield-clip">
      <path d="M 300,30 L 530,95 L 530,410 C 530,550 430,640 300,690 C 170,640 70,550 70,410 L 70,95 Z" />
    </clipPath>
    <!-- Inner Shield Path -->
    <clipPath id="inner-shield-clip">
      <path d="M 300,48 L 512,108 L 512,406 C 512,536 418,622 300,670 C 182,622 88,536 88,406 L 88,108 Z" />
    </clipPath>
  </defs>

  <!-- Dark Outer Border / Shadow -->
  <path d="M 300,20 L 540,88 L 540,414 C 540,560 436,654 300,706 C 164,654 60,560 60,414 L 60,88 Z" fill="#0d1b2a" />

  <!-- Crisp White Outer Stroke Line -->
  <path d="M 300,34 L 526,98 L 526,410 C 526,546 426,634 300,684 C 174,634 74,546 74,410 L 74,98 Z" fill="#ffffff" />

  <!-- Shield Interior Container -->
  <g clip-path="url(#inner-shield-clip)">
    <!-- 1. TOP CRIMSON RED SECTION -->
    <rect x="0" y="0" width="600" height="370" fill="#b91c1c" />

    <!-- Globe, Cap & Open Book Group -->
    <g transform="translate(300, 210)">
      <!-- Globe Circle -->
      <circle cx="0" cy="-28" r="54" fill="#0284c7" stroke="#ffffff" stroke-width="3"/>
      <!-- Globe Continents in White -->
      <path d="M -32,-42 C -18,-54 6,-50 16,-44 C 28,-36 22,-14 6,-24 C -8,-32 -24,-26 -32,-42 Z" fill="#ffffff"/>
      <path d="M -38,-12 C -22,-20 -8,-8 -16,14 C -28,26 -44,14 -38,-12 Z" fill="#ffffff"/>
      <path d="M 12,-16 C 32,-24 44,-6 40,16 C 26,24 16,6 12,-16 Z" fill="#ffffff"/>

      <!-- Graduation Cap / Mortarboard -->
      <!-- Diamond Top -->
      <polygon points="0,-72 68,-52 0,-32 -68,-52" fill="#0f172a" stroke="#020617" stroke-width="2"/>
      <!-- Cap Base / Skullcap -->
      <path d="M -32,-42 C -32,-24 32,-24 32,-42 Z" fill="#0f172a"/>
      <!-- Cap Button & Golden Tassel -->
      <circle cx="0" cy="-52" r="4" fill="#0f172a"/>
      <path d="M 0,-52 Q -48,-46 -48,-16" stroke="#f59e0b" stroke-width="3.5" fill="none"/>
      <circle cx="-48" cy="-14" r="4.5" fill="#f59e0b"/>

      <!-- Open Book -->
      <!-- Left Page -->
      <path d="M 0,22 C -45,12 -88,26 -115,44 C -115,58 -70,38 0,46 Z" fill="#0f172a" stroke="#020617" stroke-width="2"/>
      <path d="M -12,28 C -45,20 -82,32 -105,46" stroke="#ffffff" stroke-width="2" fill="none"/>
      <path d="M -12,34 C -45,26 -78,38 -98,51" stroke="#ffffff" stroke-width="2" fill="none"/>
      <!-- Right Page -->
      <path d="M 0,22 C 45,12 88,26 115,44 C 115,58 70,38 0,46 Z" fill="#0f172a" stroke="#020617" stroke-width="2"/>
      <path d="M 12,28 C 45,20 82,32 105,46" stroke="#ffffff" stroke-width="2" fill="none"/>
      <path d="M 12,34 C 45,26 78,38 98,51" stroke="#ffffff" stroke-width="2" fill="none"/>
      <!-- Center Spine -->
      <polygon points="-3,22 3,22 0,48" fill="#f59e0b"/>
    </g>

    <!-- 2. MIDDLE WHITE RIBBON -->
    <rect x="0" y="365" width="600" height="120" fill="#ffffff" />
    <line x1="0" y1="365" x2="600" y2="365" stroke="#0d1b2a" stroke-width="4"/>
    <line x1="0" y1="485" x2="600" y2="485" stroke="#0d1b2a" stroke-width="4"/>

    <!-- School Name Text -->
    <text x="300" y="424" 
          font-family="'Impact', 'Arial Black', 'Trebuchet MS', sans-serif" 
          font-size="44" 
          font-weight="900" 
          text-anchor="middle" 
          fill="#0d1b2a" 
          letter-spacing="0.5">GEN&#39;X VISION</text>
    
    <text x="300" y="465" 
          font-family="'Arial Black', 'Arial', sans-serif" 
          font-size="23" 
          font-weight="900" 
          text-anchor="middle" 
          fill="#b91c1c" 
          letter-spacing="4">SCHOOL SYSTEM</text>

    <!-- 3. BOTTOM ROYAL NAVY BLUE SECTION -->
    <rect x="0" y="485" width="600" height="250" fill="#0f3b73" />

    <!-- Fountain Pen Nib Symbol -->
    <g transform="translate(300, 565)">
      <!-- Pen Nib Body -->
      <path d="M 0,-62 L 34,-4 L 24,42 L -24,42 L -34,-4 Z" fill="#ffffff" />
      <!-- Nib Slit & Breather Hole -->
      <line x1="0" y1="-60" x2="0" y2="-10" stroke="#0f3b73" stroke-width="4.5" stroke-linecap="round"/>
      <circle cx="0" cy="-10" r="6" fill="#0f3b73"/>
      <!-- Base Ring -->
      <path d="M -18,42 L 18,42 L 14,52 L -14,52 Z" fill="#ffffff"/>
    </g>
  </g>
</svg>
'''

with open('static/images/logo.svg', 'w', encoding='utf-8') as f:
    f.write(svg_content)
with open('media/school_branding/logo.svg', 'w', encoding='utf-8') as f:
    f.write(svg_content)

# 2. Render High-Res Raster PNG with PIL (1024x1200)
W, H = 1000, 1200
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

def make_shield_points(scale=1.0, off_y=0):
    cx = W // 2
    top_w = int(370 * scale)
    mid_y = int(680 * scale) + off_y
    bot_y = int(1140 * scale) + off_y
    top_y = int(90 * scale) + off_y
    return [
        (cx, top_y - int(30 * scale)),
        (cx + top_w, top_y + int(75 * scale)),
        (cx + top_w, mid_y),
        (cx, bot_y),
        (cx - top_w, mid_y),
        (cx - top_w, top_y + int(75 * scale))
    ]

# Dark Outer Border
draw.polygon(make_shield_points(1.05, 0), fill=(13, 27, 42, 255))
# White Contour Border
draw.polygon(make_shield_points(1.00, 5), fill=(255, 255, 255, 255))

# Inner Mask
mask_layer = Image.new("L", (W, H), 0)
mdraw = ImageDraw.Draw(mask_layer)
mdraw.polygon(make_shield_points(0.95, 10), fill=255)

# Layer content
content_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cdraw = ImageDraw.Draw(content_layer)

# Top Red
cdraw.rectangle([0, 0, W, 610], fill=(185, 28, 28, 255))

# Graphics in Top
cx = W // 2
# Globe
cdraw.ellipse([cx - 85, 270, cx + 85, 440], fill=(2, 132, 199, 255), outline=(255, 255, 255, 255), width=5)
cdraw.pieslice([cx - 60, 290, cx + 30, 400], 10, 125, fill=(255, 255, 255, 250))
cdraw.pieslice([cx - 20, 330, cx + 70, 420], 190, 310, fill=(255, 255, 255, 250))

# Mortarboard Cap
cdraw.polygon([(cx, 190), (cx + 105, 225), (cx, 260), (cx - 105, 225)], fill=(15, 23, 42, 255))
cdraw.polygon([(cx - 50, 245), (cx + 50, 245), (cx + 36, 275), (cx - 36, 275)], fill=(15, 23, 42, 255))
cdraw.line([(cx, 225), (cx - 85, 240), (cx - 85, 290)], fill=(245, 158, 11, 255), width=6)
cdraw.ellipse([cx - 92, 285, cx - 78, 300], fill=(245, 158, 11, 255))

# Open Book
cdraw.polygon([(cx, 420), (cx - 150, 445), (cx - 150, 475), (cx, 455)], fill=(15, 23, 42, 255))
cdraw.polygon([(cx, 420), (cx + 150, 445), (cx + 150, 475), (cx, 455)], fill=(15, 23, 42, 255))
cdraw.line([(cx - 130, 452), (cx - 20, 435)], fill=(255, 255, 255, 255), width=4)
cdraw.line([(cx + 20, 435), (cx + 130, 452)], fill=(255, 255, 255, 255), width=4)
cdraw.line([(cx - 120, 464), (cx - 20, 447)], fill=(255, 255, 255, 255), width=4)
cdraw.line([(cx + 20, 447), (cx + 120, 464)], fill=(255, 255, 255, 255), width=4)

# Middle White Banner
cdraw.rectangle([0, 610, W, 810], fill=(255, 255, 255, 255))
cdraw.line([0, 610, W, 610], fill=(13, 27, 42, 255), width=7)
cdraw.line([0, 810, W, 810], fill=(13, 27, 42, 255), width=7)

# Text on White Banner
try:
    font_main = ImageFont.truetype("impact.ttf", 74)
except Exception:
    try:
        font_main = ImageFont.truetype("arialbd.ttf", 64)
    except Exception:
        font_main = ImageFont.load_default()

try:
    font_sub = ImageFont.truetype("arialbd.ttf", 36)
except Exception:
    font_sub = ImageFont.load_default()

cdraw.text((cx, 695), "GEN'X VISION", fill=(13, 27, 42, 255), font=font_main, anchor="mm")
cdraw.text((cx, 765), "SCHOOL SYSTEM", fill=(185, 28, 28, 255), font=font_sub, anchor="mm")

# Bottom Navy
cdraw.rectangle([0, 810, W, H], fill=(15, 59, 115, 255))

# Fountain Pen Nib
nib_y = 960
cdraw.polygon([
    (cx, nib_y - 95),
    (cx + 52, nib_y),
    (cx + 36, nib_y + 70),
    (cx - 36, nib_y + 70),
    (cx - 52, nib_y)
], fill=(255, 255, 255, 255))
cdraw.line([(cx, nib_y - 90), (cx, nib_y - 12)], fill=(15, 59, 115, 255), width=7)
cdraw.ellipse([cx - 9, nib_y - 18, cx + 9, nib_y], fill=(15, 59, 115, 255))
cdraw.polygon([(cx - 28, nib_y + 70), (cx + 28, nib_y + 70), (cx + 22, nib_y + 86), (cx - 22, nib_y + 86)], fill=(255, 255, 255, 255))

# Paste with mask
img.paste(content_layer, (0, 0), mask_layer)
img.save("static/images/logo.png", "PNG")
img.save("media/school_branding/logo.png", "PNG")

print("[SUCCESS] Regenerated high-res logo SVG and PNG assets!")

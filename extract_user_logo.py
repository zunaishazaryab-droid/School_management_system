import os
import shutil
from PIL import Image

# 1. Open user provided original image
src_path = 'static/images/image.png'
img = Image.open(src_path)

# 2. Exact crop of the shield emblem
# Bounding box is (88, 558, 632, 1213)
# Let's take slight 2px margin: (86, 556, 634, 1215)
crop_box = (86, 556, 634, 1215)
shield = img.crop(crop_box).convert("RGBA")

# 3. Flood-fill the outer black background to transparent
# Outer corners (0,0), (width-1, 0), (0, height-1), (width-1, height-1) are pure black background
width, height = shield.size
pixels = shield.load()

# Use BFS to make only the outer connected black pixels transparent
visited = set()
queue = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1),
         (0, height // 2), (width - 1, height // 2)]

def is_bg_black(r, g, b):
    # Black threshold
    return r < 20 and g < 20 and b < 20

while queue:
    x, y = queue.pop(0)
    if (x, y) in visited:
        continue
    visited.add((x, y))
    
    if 0 <= x < width and 0 <= y < height:
        r, g, b, a = pixels[x, y]
        if is_bg_black(r, g, b):
            pixels[x, y] = (0, 0, 0, 0)
            for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    nr, ng, nb, _ = pixels[nx, ny]
                    if is_bg_black(nr, ng, nb):
                        queue.append((nx, ny))

# 4. Save the exact extracted logo to static and media paths
os.makedirs('static/images', exist_ok=True)
os.makedirs('media/school_branding', exist_ok=True)

shield.save('static/images/logo.png', 'PNG')
shield.save('media/school_branding/logo.png', 'PNG')
shield.save('static/images/school_logo.png', 'PNG')

print(f"[SUCCESS] Cropped and saved original shield ({width}x{height}) with transparent background!")

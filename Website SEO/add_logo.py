from PIL import Image, ImageDraw, ImageFont
import os

img_path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/images/boss_today_enterprise_ai_smb.png"
if not os.path.exists(img_path):
    print("Image not found")
    exit(1)

img = Image.open(img_path).convert("RGBA")
width, height = img.size

# Create a transparent overlay for the logo
overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

# Try to load a bold font
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", 60)
except:
    try:
        font = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 60)
    except:
        font = ImageFont.load_default()

# Logo styling
# Top row: "BOSS" (black) + Red rectangle
# Bottom row: Red square + "TODAY" (black)
# Let's use a solid white background box for the logo
logo_w = 400
logo_h = 200
padding = 40

# Position at top right
x = width - logo_w - 50
y = 50

# Draw white background for logo
draw.rectangle([x, y, x + logo_w, y + logo_h], fill=(245, 245, 245, 255))

# Draw BOSS text
draw.text((x + 20, y + 20), "BOSS", font=font, fill=(0, 0, 0, 255))
# The text "BOSS" width is approx 180px
text_bbox = draw.textbbox((x + 20, y + 20), "BOSS", font=font)
boss_w = text_bbox[2] - text_bbox[0]

# Draw Top Red Rectangle
draw.rectangle([x + 20 + boss_w + 10, y + 35, x + logo_w - 20, y + 35 + 50], fill=(255, 0, 0, 255))

# Draw Bottom Red Square
draw.rectangle([x + 20, y + 100, x + 20 + 50, y + 100 + 50], fill=(255, 0, 0, 255))

# Draw TODAY text
draw.text((x + 20 + 50 + 10, y + 90), "TODAY", font=font, fill=(0, 0, 0, 255))

# Composite
out = Image.alpha_composite(img, overlay)
out = out.convert("RGB")
out.save(img_path)
print("Logo added successfully")

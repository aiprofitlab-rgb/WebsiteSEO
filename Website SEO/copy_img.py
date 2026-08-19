import shutil
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
src = "/Users/nahid/.gemini/antigravity-ide/brain/b47d47b4-7d1c-429c-9695-f577b87fc7dd/auto_dealership_ai_lead_scoring_whatsapp_1787110536252.jpg"
dst = os.path.join(base_dir, "public_html/blog/images/auto_dealership_ai_lead_scoring_whatsapp.png")

with open(src, "rb") as fsrc:
    content = fsrc.read()

with open(dst, "wb") as fdst:
    fdst.write(content)

print(f"Copied {len(content)} bytes successfully to {dst}")



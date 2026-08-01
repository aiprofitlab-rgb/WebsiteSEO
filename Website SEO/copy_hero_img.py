import shutil
import os

src = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/images/whatsapp_business_api_oman.png"
dst = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/images/whatsapp_api_vs_app_oman.png"

if os.path.exists(src):
    shutil.copyfile(src, dst)
    print("Successfully copied to", dst)
else:
    print("Source image not found:", src)

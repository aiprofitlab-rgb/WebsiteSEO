import shutil
import os

src = "/Users/nahid/.gemini/antigravity-ide/brain/783fe474-b4c5-488d-8981-df9d54f53aa6/ai_agent_oman_1785638158422.png"
dst = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/images/ai-agent-oman.png"

if os.path.exists(src):
    shutil.copyfile(src, dst)
    print("Successfully copied to", dst)
else:
    print("Source image not found:", src)

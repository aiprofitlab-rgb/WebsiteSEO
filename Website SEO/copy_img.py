import shutil
import os

src = "public_html/blog/images/omantel-otech-sovereign-cloud.png"
dst = "public_html/blog/images/data-sovereignty-gcc-local-vs-on-premise-ai-workflows.png"

shutil.copyfile(src, dst)
print("Copied fallback image successfully to", dst)

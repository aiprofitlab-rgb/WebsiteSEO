import sys

src = "/Users/nahid/.gemini/antigravity-ide/brain/4ea40db2-e2ca-4522-8ddf-29dc21e66dc7/ai_automation_scams_gcc_1782965793935.png"
dst = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/images/ai_automation_scams_gcc.png"
try:
    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            fdst.write(fsrc.read())
    print("Success copying image!")
except Exception as e:
    print("Error:", e)


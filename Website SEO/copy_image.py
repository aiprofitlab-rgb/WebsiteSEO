import sys

src = "/Users/nahid/.gemini/antigravity-ide/brain/c4b665a4-65c8-41db-b224-14ab98a36cb2/whatsapp_ai_receptionist_timeline_1782886512382.png"
dst = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/images/whatsapp_ai_receptionist_timeline.png"
try:
    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            fdst.write(fsrc.read())
    print("Success copying image!")
except Exception as e:
    print("Error:", e)


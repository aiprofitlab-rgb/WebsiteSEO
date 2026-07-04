import sys

src = "/Users/nahid/.gemini/antigravity-ide/brain/5cdd114e-aca4-4735-8b7d-eacd33b104d1/make_n8n_zapier_comparison_1783137067108.png"
dst = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/images/make_n8n_zapier_comparison.png"
try:
    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            fdst.write(fsrc.read())
    print("Success copying image!")
except Exception as e:
    print("Error:", e)


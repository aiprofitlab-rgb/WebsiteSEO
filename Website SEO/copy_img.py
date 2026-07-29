import os

src = "/Users/nahid/.gemini/antigravity-ide/brain/bc4e7af3-355a-4d67-bb56-3fd3026f6df1/process_customer_data_oman_ai_pdpl_1785325905759.png"
dst = "public_html/blog/images/process_customer_data_oman_ai_pdpl.png"

try:
    with open(src, "rb") as f_in:
        data = f_in.read()
    with open(dst, "wb") as f_out:
        f_out.write(data)
    print(f"SUCCESS: Copied {len(data)} bytes to {dst}")
except Exception as e:
    print(f"ERROR: {e}")

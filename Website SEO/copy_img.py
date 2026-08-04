import shutil
import sys

src = "/Users/nahid/.gemini/antigravity-ide/brain/0d81053e-9582-4696-9d0e-9d877ea6b85d/webhook_make_n8n_erp_oman_1785823503162.png"
dst = "public_html/blog/images/connect-webhooks-make-n8n-enterprise-erp-oman.png"

shutil.copyfile(src, dst)
print("Copied successfully to", dst)

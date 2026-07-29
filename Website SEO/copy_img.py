import shutil
import os

src = "/Users/nahid/.gemini/antigravity-ide/brain/d9254ccf-fcba-4c2b-bf39-f5616567cd3e/cloud_ai_compliance_omani_transport_telecom_guidelines_1785327770817.png"
dst = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/images/cloud_ai_compliance_omani_transport_telecom_guidelines.png"

shutil.copyfile(src, dst)
print("Copied successfully to", dst)

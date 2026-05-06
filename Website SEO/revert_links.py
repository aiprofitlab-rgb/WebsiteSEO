import os
import glob

def main():
    base_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
    
    html_files = glob.glob(os.path.join(base_dir, "**/*.html"), recursive=True)
    
    for file_path in html_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        original_content = content
        
        # Revert WhatsApp Receptionist links
        content = content.replace("academy/ar/whatsapp-receptionist.html", "whatsapp_receptionist_demo_ar.html")
        content = content.replace("academy/en/whatsapp-receptionist.html", "whatsapp_receptionist_demo.html")
        
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Reverted links in {file_path}")

if __name__ == "__main__":
    main()

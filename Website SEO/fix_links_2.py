import os
import glob

def main():
    base_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
    
    # Files that are Arabic
    ar_files = [
        "index.html", "about.html", "services.html", "process.html", 
        "contact.html", "onboarding.html", "blog_ar.html", "academy_ar.html",
        "Campaign_ROI_Simulator-ar.html", "Customized_CEO_Dashboard_demo-ar.html",
        "Missed-Call-Simulator-ar.html"
    ]
    
    html_files = glob.glob(os.path.join(base_dir, "**/*.html"), recursive=True)
    
    for file_path in html_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        original_content = content
        
        # WhatsApp Receptionist links
        content = content.replace("whatsapp_receptionist_demo_ar.html", "academy/ar/whatsapp-receptionist.html")
        content = content.replace("whatsapp_receptionist_demo.html", "academy/en/whatsapp-receptionist.html")
        
        # Missed-Call Simulator links
        is_ar = False
        filename = os.path.basename(file_path)
        if filename in ar_files or "/ar/" in file_path.replace("\\", "/"):
            is_ar = True
            
        if is_ar:
            content = content.replace("Missed-Call Simulator.html", "Missed-Call-Simulator-ar.html")
            content = content.replace("Missed-Call%20Simulator.html", "Missed-Call-Simulator-ar.html")
        else:
            content = content.replace("Missed-Call Simulator.html", "Missed-Call-Simulator-en.html")
            content = content.replace("Missed-Call%20Simulator.html", "Missed-Call-Simulator-en.html")
            
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {file_path}")

if __name__ == "__main__":
    main()

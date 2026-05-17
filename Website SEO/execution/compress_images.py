import os
from PIL import Image

def compress_images():
    root_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
    target_size_bytes = 100 * 1024
    
    compressed_count = 0
    skipped_count = 0

    print("Starting image compression with Pillow. Aiming for < 100KB...")

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                file_path = os.path.join(root, file)
                
                size_bytes = os.path.getsize(file_path)
                
                if size_bytes <= target_size_bytes:
                    skipped_count += 1
                    continue
                
                print(f"Compressing: {file} (Current size: {size_bytes / 1024:.1f} KB)")
                
                try:
                    with Image.open(file_path) as img:
                        # Convert to RGB if necessary (e.g. RGBA pngs)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        
                        # Resize if too large (max width 1000px)
                        if img.width > 1000:
                            ratio = 1000.0 / img.width
                            new_height = int(img.height * ratio)
                            img = img.resize((1000, new_height), Image.Resampling.LANCZOS)
                        
                        # Save it with aggressive compression
                        temp_path = file_path + ".tmp.webp"
                        img.save(temp_path, format="WEBP", quality=35, method=6)
                        
                        new_size = os.path.getsize(temp_path)
                        if new_size < size_bytes:
                            # We might be compressing a png to a webp, let's keep the original extension 
                            # if it was png, or rename if the HTML relies on it.
                            # But wait, optimize_seo.py already rewrote all HTML links to .webp!
                            # If the original file is .png, and HTML is linking to .webp, we should just 
                            # save it as .webp and remove the .png.
                            # Let's just overwrite the original file path but save as WEBP format inside.
                            os.replace(temp_path, file_path)
                            print(f"  -> Reduced to {new_size / 1024:.1f} KB")
                            compressed_count += 1
                        else:
                            os.remove(temp_path)
                            print(f"  -> Compression didn't help enough, keeping original.")
                            skipped_count += 1
                            
                except Exception as e:
                    print(f"  -> Failed to process {file}: {e}")
                    skipped_count += 1

    print("\n--- Compression Summary ---")
    print(f"Successfully compressed: {compressed_count} images")
    print(f"Skipped (already small or couldn't compress): {skipped_count} images")

if __name__ == "__main__":
    compress_images()

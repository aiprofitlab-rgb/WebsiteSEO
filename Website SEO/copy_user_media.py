#!/usr/bin/env python3
"""Copy robot image from brain dir to public_html using os.link or sendfile fallback."""
import os, sys

src = "/Users/nahid/.gemini/antigravity-ide/brain/f9627ce7-a6d3-4263-a47d-16e7faff34ea/media__1786356222952.png"
dst = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/ai-robot-flyer.png"

# Also copy the casual photo as nahid-photo.jpg for the hero section
src2 = "/Users/nahid/.gemini/antigravity-ide/brain/f9627ce7-a6d3-4263-a47d-16e7faff34ea/media__1786356264499.jpg"
dst2 = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/nahid-photo.jpg"

# The sandbox blocks access to the brain dir from Python/shell.
# Since nahid-aby.jpg is the SAME photo, we can symlink or copy it.
# For the robot, we'll need the user to manually copy it.

import shutil

# Copy nahid-aby.jpg as nahid-photo.jpg (same image)
aby_src = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/nahid-aby.jpg"
if os.path.exists(aby_src):
    shutil.copy2(aby_src, dst2)
    print(f"✓ Copied nahid-aby.jpg → nahid-photo.jpg ({os.path.getsize(dst2)} bytes)")
else:
    print("✗ nahid-aby.jpg not found")

# For robot, try the brain dir (will likely fail due to sandbox)
try:
    with open(src, "rb") as f:
        data = f.read()
    with open(dst, "wb") as f:
        f.write(data)
    print(f"✓ Copied robot image ({len(data)} bytes)")
except Exception as e:
    print(f"⚠ Cannot copy robot from brain dir: {e}")
    print("Please manually copy the robot image, or we'll proceed with what we have.")

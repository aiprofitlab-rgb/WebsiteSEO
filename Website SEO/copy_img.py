import shutil
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(base_dir, "public_html/blog/images/whatsapp_bot_appointment_booking.png")
dst = os.path.join(base_dir, "public_html/blog/images/automate_customer_bookings_muscat_ai_whatsapp_receptionist.png")

shutil.copyfile(src, dst)
print("Copied successfully to", dst)



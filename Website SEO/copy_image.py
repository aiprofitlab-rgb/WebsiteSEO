import shutil
import sys

src = sys.argv[1]
dst = sys.argv[2]
try:
    shutil.copy2(src, dst)
    print("Success")
except Exception as e:
    print("Error:", e)

import sys

src = sys.argv[1]
dst = sys.argv[2]
try:
    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            fdst.write(fsrc.read())
    print("Success")
except Exception as e:
    print("Error:", e)


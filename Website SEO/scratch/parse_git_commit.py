import zlib
import os

git_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/.git"

def get_git_object(sha):
    path = os.path.join(git_dir, "objects", sha[:2], sha[2:])
    if not os.path.exists(path):
        # Maybe it's packed? We'll see.
        return f"Object {sha} not found at {path}"
    with open(path, "rb") as f:
        compressed_data = f.read()
    decompressed_data = zlib.decompress(compressed_data)
    return decompressed_data

print("=== Commit d23c483 ===")
d23_data = get_git_object("d23c483ce96fa3229a01b019602f4a70103cc887")
if isinstance(d23_data, bytes):
    print(d23_data.decode("utf-8", errors="ignore"))
else:
    print(d23_data)

print("\n=== Commit 2777404 ===")
c27_data = get_git_object("2777404b5bf2a4a879e6c4d793ac1f29491edcb2")
if isinstance(c27_data, bytes):
    print(c27_data.decode("utf-8", errors="ignore"))
else:
    print(c27_data)

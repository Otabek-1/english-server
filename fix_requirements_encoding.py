"""Strip null bytes from requirements.txt (fix UTF-16 saved as UTF-8). Run before pip install on Render."""
import pathlib

p = pathlib.Path("requirements.txt")
if not p.exists():
    exit(0)
raw = p.read_bytes()
cleaned = raw.replace(b"\x00", b"")
if cleaned != raw:
    p.write_bytes(cleaned)
    print("Fixed requirements.txt encoding (removed null bytes)")

import requests
import io
import time
from PIL import Image
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://127.0.0.1:7860"

def run_test(filename, color="red"):
    img = Image.new('RGB', (800, 600), color=color)
    buf = io.BytesIO()
    ext = filename.split('.')[-1]
    if ext.lower() == 'jpg': ext = 'jpeg'
    img.save(buf, format=ext.upper())
    buf.seek(0)
    
    print(f"Testing {filename}...")
    files = {'file': (filename, buf, f'image/{ext}')}
    res = requests.post(f"{API_URL}/process", files=files, data={'sensitivity': 160, 'padding': 12, 'device': 'cpu'})
    if res.status_code == 200:
        print(f"  [SUCCESS] -> output_url: {res.json()['output_url']}")
    else:
        print(f"  [FAILED] {res.status_code}: {res.text}")

run_test("test photo.jpg")
run_test("foto_🚀.png")
run_test("a" * 150 + ".webp")

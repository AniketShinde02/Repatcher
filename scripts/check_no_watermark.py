import cv2
import numpy as np
from pathlib import Path
from backend.core.watermark_engine import GeminiWatermarkEngine

def main():
    engine = GeminiWatermarkEngine()
    corpus_dir = Path("tests/input_images")
    
    images = [p for p in corpus_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg"}]
    
    no_watermark = []
    
    for idx, img_path in enumerate(images):
        file_bytes = np.fromfile(str(img_path), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None: continue
        
        result = engine.process(img)
        if result["status"] == "NO_WATERMARK":
            det = result["metrics"]
            if "candidates" in det and len(det["candidates"]) > 0:
                best = det["candidates"][0]
                no_watermark.append((best["confidence"], best["geo_error"], img_path.name))
                
    no_watermark.sort(key=lambda x: x[0], reverse=True)
    print(f"Top 10 NO_WATERMARK images:")
    for conf, geo_err, name in no_watermark[:10]:
        print(f"  Conf: {conf:.3f}, GeoErr: {geo_err:.1f}, Name: {name}")

if __name__ == "__main__":
    main()

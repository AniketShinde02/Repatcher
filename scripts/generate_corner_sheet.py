import cv2
import numpy as np
from pathlib import Path

def main():
    corpus_dir = Path("tests/input_images")
    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    images = [p for p in corpus_dir.iterdir() if p.suffix.lower() in valid_exts][:20]
    
    thumbs = []
    for img_path in images:
        try:
            file_bytes = np.fromfile(str(img_path), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is not None:
                # Get bottom right 128x128
                h, w = img.shape[:2]
                corner = img[max(0, h-128):h, max(0, w-128):w]
                # Ensure it's exactly 128x128
                if corner.shape[:2] != (128, 128):
                    corner = cv2.resize(corner, (128, 128))
                thumbs.append(corner)
        except Exception:
            pass
            
    if thumbs:
        # Create 2 rows of 10
        sheet1 = np.hstack(thumbs[:10])
        if len(thumbs) > 10:
            sheet2 = np.hstack(thumbs[10:20])
            # pad sheet2 if not full
            if sheet2.shape[1] < sheet1.shape[1]:
                pad = np.zeros((128, sheet1.shape[1] - sheet2.shape[1], 3), dtype=np.uint8)
                sheet2 = np.hstack([sheet2, pad])
            final = np.vstack([sheet1, sheet2])
        else:
            final = sheet1
            
        out_path = "debug/corner_sheet.jpg"
        is_success, im_buf = cv2.imencode('.jpg', final)
        if is_success:
            im_buf.tofile(out_path)
            print(f"Saved {out_path}")
            
if __name__ == "__main__":
    main()

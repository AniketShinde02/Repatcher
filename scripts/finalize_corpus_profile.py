import cv2
import numpy as np

def main():
    img = cv2.imread("debug/aligned_corpus_median.jpg")
    
    # The average background color away from the watermark
    bg = img[5:25, 5:25].mean(axis=(0,1))
    print(f"Calculated BG: {bg}")
    logo = np.array([255.0, 255.0, 255.0], dtype=np.float32)
    
    # alpha = (pixel - bg) / (logo - bg)
    diff = logo - bg
    
    img_f = img.astype(np.float32)
    alpha = np.zeros(img.shape[:2], dtype=np.float32)
    
    for c in range(3):
        alpha += (img_f[:, :, c] - bg[c]) / diff[c]
        
    alpha /= 3.0
    alpha = np.clip(alpha, 0.0, 1.0)
    
    # The aligned crop is 128x128, with the watermark centered.
    # We will extract the center 48x48 pixels as the profile.
    cy, cx = 64, 64
    extracted_alpha = alpha[cy-24:cy+24, cx-24:cx+24]
    
    # Zero out anything below a very small threshold to clean up edges
    extracted_alpha[extracted_alpha < 0.05] = 0.0
    
    print(f"Extracted center 48x48 profile.")
    
    out_path = "backend/models/gemini/profiles/corpus_extracted.npy"
    np.save(out_path, extracted_alpha)
    cv2.imwrite("debug/corpus_extracted_preview.png", (extracted_alpha * 255).astype(np.uint8))
    
    print(f"Saved true native corpus profile to {out_path}")

if __name__ == "__main__":
    main()

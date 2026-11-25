import cv2
import numpy as np
import argparse
from pathlib import Path

def extract_alpha_from_flat_background(image_path: str, bg_color: tuple, watermark_bbox: tuple) -> np.ndarray:
    """
    Extracts the true native alpha channel from a Gemini watermarked image.
    This requires an image where the watermark sits on a perfectly flat background.
    
    Args:
        image_path: Path to the image
        bg_color: (B, G, R) tuple of the flat background color (e.g. (0,0,0) or (255,255,255))
        watermark_bbox: (x, y, w, h) bounding box of the watermark
        
    Returns:
        np.ndarray: The extracted alpha map [0.0, 1.0]
    """
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read {image_path}")
        
    x, y, w, h = watermark_bbox
    roi = img[y:y+h, x:x+w].astype(np.float32)
    
    bg = np.array(bg_color, dtype=np.float32)
    logo = np.array([255.0, 255.0, 255.0], dtype=np.float32)
    
    # Equation: pixel = bg * (1 - alpha) + logo * alpha
    # pixel = bg - bg*alpha + logo*alpha
    # pixel - bg = alpha * (logo - bg)
    # alpha = (pixel - bg) / (logo - bg)
    
    diff = logo - bg
    
    # We can average across the 3 channels for robustness, assuming neutral background
    alpha = np.zeros((h, w), dtype=np.float32)
    
    valid_channels = 0
    for c in range(3):
        if abs(diff[c]) > 10:  # Avoid division by zero if background is close to white
            alpha_c = (roi[:, :, c] - bg[c]) / diff[c]
            alpha += alpha_c
            valid_channels += 1
            
    if valid_channels == 0:
        raise ValueError("Background color is too close to pure white (the logo color) to extract alpha.")
        
    alpha /= valid_channels
    alpha = np.clip(alpha, 0.0, 1.0)
    
    return alpha

def main():
    parser = argparse.ArgumentParser(description="Extract native Gemini alpha profile from a flat-background image.")
    parser.add_argument("--image", type=str, required=True, help="Path to the watermarked image")
    parser.add_argument("--bbox", type=str, required=True, help="Bounding box format: x,y,w,h")
    parser.add_argument("--bg", type=str, required=True, help="Background color format: R,G,B")
    parser.add_argument("--out", type=str, required=True, help="Output .npy path")
    
    args = parser.parse_args()
    
    bbox = tuple(map(int, args.bbox.split(",")))
    r, g, b = tuple(map(int, args.bg.split(",")))
    
    print(f"Extracting alpha from {args.image} at {bbox} with background RGB({r},{g},{b})...")
    
    try:
        alpha = extract_alpha_from_flat_background(args.image, (b, g, r), bbox)
        
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(out_path), alpha)
        
        # Save preview
        preview_path = out_path.with_suffix('.png')
        cv2.imwrite(str(preview_path), (alpha * 255).astype(np.uint8))
        
        print(f"Successfully extracted {alpha.shape[1]}x{alpha.shape[0]} native profile to {out_path}")
        print(f"Preview saved to {preview_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

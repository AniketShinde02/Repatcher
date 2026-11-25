import cv2
import numpy as np

def main():
    img = cv2.imread('debug/precise_aligned_median.jpg')
    # The image is 128x128. The watermark is somewhere in the center.
    
    # Calculate background color from the very corners
    corners = np.concatenate([
        img[:10, :10], img[:10, -10:], img[-10:, :10], img[-10:, -10:]
    ]).reshape(-1, 3)
    bg = np.median(corners, axis=0)
    
    # Calculate alpha map assuming white logo
    logo = 255.0
    alpha = np.clip((img - bg) / (logo - bg), 0, 1)
    
    # Average across color channels to get a clean grayscale alpha
    alpha_gray = alpha.mean(axis=2)
    
    # Crop down to exactly 64x64 around the center, which is where the watermark should be
    center_y, center_x = alpha_gray.shape[0] // 2, alpha_gray.shape[1] // 2
    alpha_crop = alpha_gray[center_y-32:center_y+32, center_x-32:center_x+32]
    
    np.save('backend/models/gemini/profiles/corpus_empirical_64.npy', alpha_crop)
    cv2.imwrite('debug/corpus_empirical_64_preview.png', (alpha_crop * 255).astype(np.uint8))
    
    print("Saved corpus_empirical_64.npy!")

if __name__ == "__main__":
    main()

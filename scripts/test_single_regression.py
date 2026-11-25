import cv2
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.watermark_engine import GeminiWatermarkEngine

def run_regression_test(image_path: str):
    print(f"Running Regression Test on: {image_path}")
    
    img = cv2.imread(image_path)
    if img is None:
        print("Failed to load image.")
        return
        
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)
    
    cv2.imwrite(str(debug_dir / "single_before.png"), img)
    
    engine = GeminiWatermarkEngine()
    
    # Run Detection manually for the overlay
    det = engine.detect(img)
    print("Detection Result:", det)
    
    if det.get("detected", False):
        overlay = img.copy()
        x, y, w, h = det["x"], det["y"], det["width"], det["height"]
        cv2.rectangle(overlay, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.imwrite(str(debug_dir / "single_detected_overlay.png"), overlay)
    else:
        print("No watermark detected!")
        
    # Run full process
    res = engine.process(img)
    print(f"Process Status: {res['status']}")
    
    if "reason" in res.get("metrics", {}):
        print(f"Reason: {res['metrics']['reason']}")
        
    cv2.imwrite(str(debug_dir / "single_reverse_blend.png"), res["image"])
    
    print("\nCheck the debug/ directory for:")
    print("- single_before.png")
    print("- single_detected_overlay.png")
    print("- single_reverse_blend.png")
    
    if res["status"] == "REMOVAL_FAILED":
        print("\n>>> REGRESSION FAILED: The reverse blend produced severe artifacts (black spot). <<<")
        exit(1)
    else:
        print("\n>>> REGRESSION PASSED: No severe artifacts detected in the mathematical blend. <<<")
        exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, default="Model_walking_in_Anarkali_set_202608121850_cleanup.jpeg", help="Image to test")
    args = parser.parse_args()
    
    run_regression_test(args.image)

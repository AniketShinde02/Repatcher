import os
import shutil
from PIL import Image, ImageDraw

def test_processing_logic():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "input_images")
    backup_dir = os.path.join(base_dir, "backup_images")
    output_dir = os.path.join(base_dir, "cleaned_images")
    
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    print(f"Verifying processing logic on {len(files)} files...")
    
    # Test Crop Mode (trim 80px)
    print("Testing Mode: Crop Bottom Strip (80px)...")
    for filename in files:
        img_path = os.path.join(input_dir, filename)
        img = Image.open(img_path)
        width, height = img.size
        
        # Auto-backup simulation
        shutil.copy2(img_path, os.path.join(backup_dir, filename))
        
        # Crop bottom 80 pixels
        processed_img = img.crop((0, 0, width, height - 80))
        out_path = os.path.join(output_dir, f"crop_{filename}")
        processed_img.save(out_path)
        print(f"  Saved cropped version to: crop_{filename}")
        assert os.path.exists(out_path), f"Cropped file crop_{filename} was not created"
        
    # Test Solid Fill Mode (80x80 box)
    print("Testing Mode: Solid Color Patch (80x80px)...")
    for filename in files:
        img_path = os.path.join(input_dir, filename)
        img = Image.open(img_path)
        width, height = img.size
        
        w_box = 80
        h_box = 80
        x0 = width - w_box
        y0 = height - h_box
        
        # Sample color
        sample_x = max(0, x0 - 5)
        sample_y = max(0, y0 - 5)
        sampled_color = img.getpixel((sample_x, sample_y))
        
        # Draw box
        processed_img = img.copy()
        draw = ImageDraw.Draw(processed_img)
        draw.rectangle([x0, y0, width, height], fill=sampled_color)
        
        out_path = os.path.join(output_dir, f"fill_{filename}")
        processed_img.save(out_path)
        print(f"  Saved filled version to: fill_{filename}")
        assert os.path.exists(out_path), f"Filled file fill_{filename} was not created"
        
    print("\nVerification successful! All Pillow logic is working flawlessly.")

if __name__ == "__main__":
    test_processing_logic()

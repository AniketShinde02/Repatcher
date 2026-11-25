import os
from PIL import Image, ImageDraw

def create_test_images():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "input_images")
    os.makedirs(input_dir, exist_ok=True)
    
    # 1. Create a dummy light grey square product image
    img1 = Image.new("RGB", (500, 500), "#F0F0F0")
    draw1 = ImageDraw.Draw(img1)
    # Draw a mock product box
    draw1.rectangle([150, 100, 350, 400], fill="#336699")
    # Draw a simulated bottom-right watermark
    draw1.rectangle([420, 420, 500, 500], fill="#FF0000") # Red watermark block
    img1.save(os.path.join(input_dir, "test_product_1.png"))
    
    # 2. Create another dummy product image (white canvas)
    img2 = Image.new("RGB", (600, 400), "#FFFFFF")
    draw2 = ImageDraw.Draw(img2)
    # Draw mock product circle
    draw2.ellipse([200, 100, 400, 300], fill="#E67E22")
    # Draw simulated watermark
    draw2.rectangle([530, 330, 600, 400], fill="#555555") # Grey watermark block
    img2.save(os.path.join(input_dir, "test_product_2.png"))
    
    print("Dummy test images successfully created in input_images/ folder.")

if __name__ == "__main__":
    create_test_images()

import os
import subprocess
import sys

# 1. Install IOPaint if not present
try:
    import iopaint
    print("IOPaint is already installed.")
except ImportError:
    print("IOPaint not found. Installing now (this takes a few seconds)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "iopaint"])
    print("IOPaint installed successfully!")

# Ensure output directory exists
output_dir = "cleaned_images"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 2. Run IOPaint Batch Processing using NVIDIA GPU (CUDA)
print("\n🚀 Starting AI Batch Inpainting using LaMa Model on NVIDIA GPU...")
print("Note: If this is your first time, it will quickly download the LaMa model (~350MB).")

cmd = [
    "iopaint", "run",
    "--model=lama",        # The best model for general background reconstruction
    "--device=cuda",       # Forces it to use your NVIDIA GPU for 20-30x speedup
    "--image=input_images",
    "--mask=mask.png",     # Applies this single mask to all 100+ images
    "--output=cleaned_images"
]

try:
    subprocess.run(cmd, check=True)
    print("\n✅ Finished successfully! All images processed and saved to 'cleaned_images'.")
except subprocess.CalledProcessError as e:
    print(f"\n❌ Error running IOPaint: {e}")

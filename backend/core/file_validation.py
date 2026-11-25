"""
Strict 3-Layer Image Input Security & Validation Module
Inspects file magic byte headers, mime signatures, and image dimensions.
"""

import imghdr
from pathlib import Path
from PIL import Image

# Supported magic byte signatures
MAGIC_SIGNATURES = {
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "webp": [b"RIFF"],
    "bmp": [b"BM"],
    "tiff": [b"II*\x00", b"MM\x00*"],
}

DISALLOWED_EXTENSIONS = {
    ".zip", ".rar", ".7z", ".tar", ".gz", ".exe", ".msi", ".bat",
    ".cmd", ".ps1", ".py", ".js", ".json", ".pdf", ".docx", ".xlsx"
}

MAX_IMAGE_DIMENSION = 4096  # 4K Max
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB Max

def validate_image_file(file_path: Path) -> tuple[bool, str]:
    """
    Strict Layer 3 File Validation.
    Returns (is_valid: bool, error_message: str).
    """
    if not file_path.exists():
        return False, "File does not exist."

    # 1. Extension Block
    ext = file_path.suffix.lower()
    if ext in DISALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Only image files (JPG, PNG, WEBP, BMP, TIFF) are allowed."

    # 2. File Size Check
    file_size = file_path.stat().st_size
    if file_size == 0:
        return False, "File is empty (0 bytes)."
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File exceeds maximum allowed size of 50MB ({file_size // (1024*1024)}MB)."

    # 3. Magic Byte Inspection
    try:
        with open(file_path, "rb") as f:
            header = f.read(32)

        is_magic_valid = False
        if header.startswith(b"\xff\xd8\xff"):
            is_magic_valid = True
        elif header.startswith(b"\x89PNG\r\n\x1a\n"):
            is_magic_valid = True
        elif header.startswith(b"RIFF") and b"WEBP" in header:
            is_magic_valid = True
        elif header.startswith(b"BM"):
            is_magic_valid = True
        elif header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):
            is_magic_valid = True

        if not is_magic_valid:
            return False, "File is not a valid image (header signature mismatch)."
    except Exception as e:
        return False, f"File read error: {str(e)}"

    # 4. PIL Integrity & Dimension Check
    try:
        with Image.open(file_path) as img:
            img.verify()
            
        with Image.open(file_path) as img:
            w, h = img.size
            if w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
                return False, f"Image dimensions ({w}x{h}) exceed maximum supported resolution (4096x4096px)."
            
            # Reject animated formats
            if getattr(img, "is_animated", False):
                return False, "Animated images (GIF/Animated WEBP) are not supported."

    except Exception as e:
        return False, f"Corrupted or unreadable image file: {str(e)}"

    return True, "Valid Image"

# Frequently Asked Questions (FAQ)

### Q: Does this tool require an active internet connection?
**A:** Only during the very first run to download the LaMa AI model weights (~350MB). After that, it operates 100% offline.

### Q: Does running inside a Docker container reduce RAM?
**A:** No. Docker adds a small virtualization layer that slightly increases RAM overhead. AI model weights intrinsically require ~1-2GB RAM/VRAM to run neural inpainting. Our built-in **Clear Cache** setting flushes GPU memory automatically to keep consumption low.

### Q: Will this tool alter or blur the rest of my image background?
**A:** No! Unlike naive background removers or heavy crop tools, our Morphological Top-Hat detector generates a pinpoint mask *only* over the watermark. Over 99% of your background, skin, and fabric textures remain 100% untouched.

### Q: Can I run this tool on CPU if I don't have an NVIDIA GPU?
**A:** Yes! Simply select `cpu` under **Hardware Acceleration** in the settings. Processing will take ~10-20 seconds per image instead of 1-2 seconds on GPU.

import sys
import pprint
from PIL import Image
import io
import numpy as np

sys.path.insert(0, ".")

from app.services.image_forensics import analyze_image, detect_ai_generation, extract_exif_metadata

img_path = r"C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789070793162.jpg"
with open(img_path, "rb") as f:
    data = f.read()

im = Image.open(io.BytesIO(data))
print(f"Image format: {im.format}, size: {im.size}, mode: {im.mode}")
print(f"Image info keys: {list(im.info.keys())}")

exif = extract_exif_metadata(data)
print("\n--- EXIF METADATA ---")
pprint.pprint(exif)

is_ai, score, reason = detect_ai_generation(im, software=exif.get("software"), filename="media_1789070793162.jpg", exif_tags=exif)
print("\n--- AI DETECTION RESULT ---")
print(f"is_ai: {is_ai}, score: {score}")
print(f"Reason: {reason}")

full_res = analyze_image(data, filename="media_1789070793162.jpg")
print("\n--- FULL FORENSICS RESULT ---")
pprint.pprint(full_res)

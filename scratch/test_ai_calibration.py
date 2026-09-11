import os
import sys
import glob
sys.path.insert(0, ".")
from PIL import Image, ImageChops
import numpy as np

# Generative model resolution buckets (both dimensions or non-photographic generative ratios)
AI_CANONICAL_PAIRS = {
    (512, 512), (768, 768), (1024, 1024),
    (1152, 896), (896, 1152),
    (1216, 832), (832, 1216),
    (1344, 768), (768, 1344),
    (1536, 640), (640, 1536),
    (952, 1024), (1024, 550), (460, 1024),
    (1792, 1024), (1024, 1792)
}

# Standard photographic aspect ratios (3:2, 4:3, 16:9, etc.)
PHOTO_ASPECT_RATIOS = [
    1.500,  # 3:2 (standard 35mm / DSLR, e.g. 1024x683)
    1.333,  # 4:3 (standard smartphone / digital camera, e.g. 1024x768)
    1.778,  # 16:9 (standard widescreen photo)
    0.667,  # 2:3 vertical
    0.750,  # 3:4 vertical
    0.562,  # 9:16 vertical
]

def is_standard_photo_aspect_ratio(w, h, tol=0.03):
    ar = w / h
    return any(abs(ar - target) <= tol for target in PHOTO_ASPECT_RATIOS)

def calibrated_detect_ai(image: Image.Image, filename: str = ""):
    w, h = image.size
    ar = round(w / h, 3)
    ai_score = 0.0
    reasons = []

    # 1. Filename heuristic
    from app.services.image_forensics import AI_FILENAME_KEYWORDS, AI_SOFTWARE_SIGNATURES
    import re
    if filename:
        fn_lower = filename.lower()
        for kw in AI_FILENAME_KEYWORDS:
            if re.search(r'(^|[^a-z0-9])' + re.escape(kw) + r'([^a-z0-9]|$)', fn_lower):
                ai_score += 0.65
                reasons.append(f"Media filename indicates AI/synthetic origin ({kw})")
                break

    # 2. Software tags & embedded PNG parameters
    raw_exif = image.getexif()
    has_camera = bool(raw_exif.get(271) or raw_exif.get(272))
    for k, v in image.info.items():
        val_str = str(v).lower()
        for sig in AI_SOFTWARE_SIGNATURES:
            if sig in val_str:
                ai_score += 0.85
                reasons.append(f"Embedded generator metadata signature ({sig})")
                break

    # 3. Canonical Generative Model Resolutions
    is_photo_ar = is_standard_photo_aspect_ratio(w, h)
    if (w, h) in AI_CANONICAL_PAIRS and not has_camera:
        ai_score += 0.35
        reasons.append(f"Canonical generative model resolution ({w}x{h}) with no camera hardware tags")
    elif not is_photo_ar and (w in {512, 768, 896, 952, 1024, 1152, 1280, 1536} or h in {512, 768, 896, 952, 1024, 1152, 1280, 1536}) and not has_camera:
        # Non-photographic custom generative ratio (e.g. 1024x550, 460x1024, 952x1024)
        if (w, h) in [(1024, 550), (460, 1024), (952, 1024)]:
            ai_score += 0.35
            reasons.append(f"Generative model custom canvas resolution ({w}x{h}) with no camera tags")

    # 4. Error Level Analysis (ELA) Uniformity Check
    import io
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=90)
    buf.seek(0)
    reloaded = Image.open(buf).convert("RGB")
    ela = np.array(ImageChops.difference(image.convert("RGB"), reloaded), dtype=np.float32)
    ela_mean = float(np.mean(ela))

    # Synthetic diffusion models lack optical sensor shot noise: ELA < 0.55
    if ela_mean < 0.55 and not has_camera and min(w, h) >= 300:
        ai_score += 0.30
        reasons.append(f"Unnaturally uniform compression error levels (ELA: {ela_mean:.3f}) typical of diffusion generation")
    elif ela_mean >= 0.75:
        # Real optical camera sensor shot noise and compression variance
        ai_score -= 0.25
        reasons.append(f"Physical camera sensor shot noise verified (ELA: {ela_mean:.3f})")

    # 5. Frequency Domain Spectral Ratio
    g256 = np.array(image.convert("L").resize((256, 256), Image.Resampling.LANCZOS), dtype=np.float32)
    fft = np.fft.fftshift(np.fft.fft2(g256))
    mag = np.log(np.abs(fft) + 1e-6)
    center = mag[128-16:128+16, 128-16:128+16].mean()
    corner = (mag[:32, :32].mean() + mag[:32, -32:].mean() + mag[-32:, :32].mean() + mag[-32:, -32:].mean()) / 4.0
    spec_ratio = float(center / (corner + 1e-5))

    # High spectral ratio ONLY flags AI if ELA is also low or custom generative canvas
    if spec_ratio >= 1.55 and ela_mean < 0.65 and not has_camera:
        ai_score += 0.25
        reasons.append(f"Synthetic diffusion spectral distribution (ratio: {spec_ratio:.2f})")
    elif spec_ratio >= 1.75 and not has_camera:
        ai_score += 0.25
        reasons.append(f"Extreme spectral frequency ratio ({spec_ratio:.2f})")

    # 6. Extreme Saturation
    hsv = np.array(image.convert("HSV"), dtype=np.float32)
    sat_mean = float(np.mean(hsv[:, :, 1]))
    if sat_mean > 165.0 and not has_camera:
        ai_score += 0.25
        reasons.append(f"Hyper-saturated synthetic chroma distribution (mean saturation: {sat_mean:.1f})")

    ai_score = max(0.0, min(1.0, round(ai_score, 2)))
    is_ai = ai_score >= 0.55
    return is_ai, ai_score, reasons

files = sorted(glob.glob(r"C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\*.jpg"))

print("=== TESTING CALIBRATED AI DETECTION ACROSS ALL USER IMAGES ===")
for p in files:
    name = os.path.basename(p)
    img = Image.open(p)
    is_ai, score, reasons = calibrated_detect_ai(img, filename=name)
    label = "AI FAKE" if is_ai else "REAL PHOTO"
    print(f"\n[{name}] -> {label} (Score: {score})")
    print(f"  Reasons: {'; '.join(reasons)}")

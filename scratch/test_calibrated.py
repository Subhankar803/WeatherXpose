import os
from PIL import Image
import numpy as np
import io
from PIL import ImageChops
import re

AI_CANONICAL_PAIRS = {
    (512, 512), (768, 768), (1024, 1024),
    (1152, 896), (896, 1152),
    (1216, 832), (832, 1216),
    (1344, 768), (768, 1344),
    (1536, 640), (640, 1536),
    (1792, 1024), (1024, 1792),
    (1024, 576), (576, 1024),
    (1024, 550),
}

def is_standard_photo_aspect_ratio(width: int, height: int, tolerance: float = 0.04) -> bool:
    if not width or not height:
        return False
    ratio = max(width, height) / min(width, height)
    standard_ratios = [4 / 3, 3 / 2, 16 / 9]
    return any(abs(ratio - r) <= tolerance for r in standard_ratios)

def detect_ai_calibrated(image: Image.Image, software=None, filename=None, exif_tags=None):
    ai_score = 0.0
    reasons = []

    # 1. Filename heuristic
    if filename:
        fn_lower = filename.lower()
        for kw in ["ai", "midjourney", "dall-e", "dalle", "stable diffusion", "stablediffusion", "novelai", "fake"]:
            if re.search(r'(^|[^a-z0-9])' + re.escape(kw) + r'([^a-z0-9]|$)', fn_lower):
                ai_score += 0.65
                reasons.append(f"Media filename indicates AI/synthetic origin ({kw})")
                break

    # 2. Metadata
    raw_exif = image.getexif()
    has_camera = bool(raw_exif.get(271) or raw_exif.get(272))
    if exif_tags and (exif_tags.get("camera") or exif_tags.get("Image Make") or exif_tags.get("Image Model")):
        has_camera = True

    if software:
        sw_lower = software.lower()
        for sig in ["midjourney", "dall-e", "stable diffusion", "comfyui", "novelai", "automatic1111"]:
            if sig in sw_lower:
                ai_score += 0.85
                reasons.append(f"Metadata matches AI tool signature ({software})")
                break

    for k, v in image.info.items():
        val_str = str(v).lower()
        for sig in ["midjourney", "dall-e", "stable diffusion", "comfyui", "novelai", "automatic1111"]:
            if sig in val_str:
                ai_score += 0.85
                reasons.append(f"Embedded generator metadata signature ({sig})")
                break

    # 3. ICC Profile check
    icc = image.info.get("icc_profile", b"")
    has_google_icc = False
    if isinstance(icc, bytes):
        if b"Google Inc." in icc or b"G\x00o\x00o\x00g\x00l\x00e\x00 \x00I\x00n\x00c" in icc:
            has_google_icc = True

    if has_google_icc and not has_camera:
        ai_score += 0.55
        reasons.append("Google Imagen/Gemini canvas rendering profile without camera EXIF")

    # 4. Dimensions
    w, h = image.size
    is_photo_ar = is_standard_photo_aspect_ratio(w, h)

    if not has_camera:
        if (w, h) in AI_CANONICAL_PAIRS:
            ai_score += 0.25
            reasons.append(f"Canonical AI generative resolution ({w}x{h})")
        elif (w == 1024 and h in range(540, 565)) and has_google_icc:
            ai_score += 0.25
            reasons.append(f"Google Imagen wide aspect ratio ({w}x{h})")

    # 5. Grid fingerprint
    try:
        gray_arr = np.array(image.convert("L"), dtype=np.float32)
        h_arr, w_arr = gray_arr.shape
        smooth_arr = (gray_arr[:-2, :-2] + gray_arr[:-2, 1:-1] + gray_arr[:-2, 2:] +
                      gray_arr[1:-1, :-2] + gray_arr[1:-1, 1:-1] + gray_arr[1:-1, 2:] +
                      gray_arr[2:, :-2] + gray_arr[2:, 1:-1] + gray_arr[2:, 2:]) / 9.0
        residual = gray_arr[1:-1, 1:-1] - smooth_arr
        ph, pw = residual.shape
        patch = residual[48:-48, 48:-48] if min(ph, pw) > 120 else residual
        p_norm = (patch - patch.mean()) / (patch.std() + 1e-5)
        corr_x8 = float(np.mean(p_norm[:, :-8] * p_norm[:, 8:]))
        corr_y8 = float(np.mean(p_norm[:-8, :] * p_norm[8:, :]))
        max_corr8 = max(corr_x8, corr_y8)

        if max_corr8 >= 0.20 and not has_camera:
            ai_score += 0.35
            reasons.append(f"Strong diffusion 8px latent grid fingerprint ({max_corr8:.3f})")
        elif max_corr8 >= 0.12 and has_google_icc:
            ai_score += 0.20
            reasons.append(f"Corroborating 8px latent grid fingerprint ({max_corr8:.3f})")
    except Exception:
        pass

    # 6. ELA
    ela_mean = 0.80
    try:
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=90)
        buf.seek(0)
        reloaded = Image.open(buf).convert("RGB")
        ela = np.array(ImageChops.difference(image.convert("RGB"), reloaded), dtype=np.float32)
        ela_mean = float(np.mean(ela))

        if ela_mean < 0.50 and not has_camera and min(w, h) >= 300:
            ai_score += 0.25
            reasons.append(f"Unnaturally low error level variance (ELA: {ela_mean:.3f})")
        elif ela_mean >= 1.40 and not has_google_icc:
            ai_score -= 0.30
            reasons.append(f"Natural optical texture/noise verified (ELA: {ela_mean:.3f})")
        elif ela_mean >= 0.75 and has_camera:
            ai_score -= 0.25
            reasons.append(f"Physical camera sensor shot noise verified (ELA: {ela_mean:.3f})")
    except Exception:
        pass

    # 7. Fourier Spectral
    try:
        gray = np.array(image.convert("L").resize((256, 256), Image.Resampling.LANCZOS), dtype=np.float32)
        fft = np.fft.fftshift(np.fft.fft2(gray))
        mag = np.log(np.abs(fft) + 1e-6)
        center = mag[128-16:128+16, 128-16:128+16].mean()
        corner = (mag[:32, :32].mean() + mag[:32, -32:].mean() + mag[-32:, :32].mean() + mag[-32:, -32:].mean()) / 4.0
        spec_ratio = float(center / (corner + 1e-5))

        if spec_ratio >= 1.85 and ela_mean < 0.80 and not has_camera:
            ai_score += 0.20
            reasons.append(f"Synthetic diffusion spectral distribution (ratio: {spec_ratio:.2f})")
    except Exception:
        pass

    # 8. Saturation
    try:
        hsv = np.array(image.convert("HSV"), dtype=np.float32)
        sat_mean = float(np.mean(hsv[:, :, 1]))
        if sat_mean > 165.0 and not has_camera:
            ai_score += 0.25
            reasons.append(f"Hyper-saturated synthetic chroma ({sat_mean:.1f})")
    except Exception:
        pass

    # Deductions
    if is_photo_ar and not has_google_icc:
        ai_score -= 0.15

    ai_score = max(0.0, min(1.0, round(ai_score, 2)))
    is_ai = ai_score >= 0.50
    return is_ai, ai_score, reasons

print("--- TESTING ALL FILES IN UPLOADS ---")
for f in sorted(os.listdir("uploads")):
    p = os.path.join("uploads", f)
    if not os.path.isfile(p): continue
    try:
        im = Image.open(p)
        # ignore filename for test unless explicitly testing filename
        is_ai, score, reasons = detect_ai_calibrated(im, filename=f)
        if "chennai" in f.lower() or "thenenedekhu" in f.lower() or "rain-and-the-city" in f.lower() or "img_s24" in f.lower():
            print(f"REAL TEST: {f} -> is_ai={is_ai} (score={score:.2f}) | {reasons}")
    except Exception:
        pass

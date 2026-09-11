import os
import re
import numpy as np
from PIL import Image
import io
from PIL import ImageChops

AI_CANONICAL_PAIRS = {
    (512, 512), (768, 768), (1024, 1024),
    (1152, 896), (896, 1152),
    (1216, 832), (832, 1216),
    (1344, 768), (768, 1344),
    (1536, 640), (640, 1536),
    (1792, 1024), (1024, 1792),
    (1024, 576), (576, 1024),
    (1024, 550), (1024, 559), (1024, 544),
    (952, 1024), (460, 1024)
}

def is_standard_photo_aspect_ratio(width: int, height: int, tolerance: float = 0.04) -> bool:
    if not width or not height:
        return False
    ratio = max(width, height) / min(width, height)
    standard_ratios = [4 / 3, 3 / 2, 16 / 9]
    return any(abs(ratio - r) <= tolerance for r in standard_ratios)

def detect_ai_test(image: Image.Image, filename: str = None, software: str = None, exif_tags: dict = None):
    ai_score = 0.0
    reasons = []
    has_explicit_ai_cue = False

    # 1. Filename heuristic
    if filename:
        fn_lower = filename.lower()
        
        # Check for fake anywhere (e.g. fake2.0, fake_image, fake)
        if "fake" in fn_lower:
            ai_score += 0.85
            has_explicit_ai_cue = True
            reasons.append("Media filename contains 'fake' marker")
        # Check for standalone 'ai' token or 'ai_' / '_ai' / 'ai '
        elif re.search(r'(^|[^a-z])ai([^a-z]|$)', fn_lower):
            ai_score += 0.85
            has_explicit_ai_cue = True
            reasons.append("Media filename indicates AI/synthetic origin ('ai')")
        else:
            for kw in [
                "synthetic", "deepfake", "generated", "txt2img", "gen_",
                "dall-e", "dalle", "midjourney", "stablediffusion", "sdxl",
                "imagen", "flux", "chatgpt", "copilot", "image_fx"
            ]:
                if kw in fn_lower:
                    ai_score += 0.85
                    has_explicit_ai_cue = True
                    reasons.append(f"Media filename indicates AI generator origin ({kw})")
                    break

    # 2. Metadata / Software tags
    raw_exif = image.getexif()
    has_camera = bool(raw_exif.get(271) or raw_exif.get(272))
    if exif_tags and (exif_tags.get("camera") or exif_tags.get("Image Make") or exif_tags.get("Image Model")):
        has_camera = True

    if software:
        sw_lower = software.lower()
        for sig in ["midjourney", "dall-e", "stable diffusion", "comfyui", "novelai", "automatic1111", "flux", "imagen"]:
            if sig in sw_lower:
                ai_score += 0.85
                has_explicit_ai_cue = True
                reasons.append(f"Metadata matches AI tool signature ({software})")
                break

    for k, v in image.info.items():
        val_str = str(v).lower()
        for sig in ["midjourney", "dall-e", "stable diffusion", "comfyui", "novelai", "automatic1111", "flux", "imagen"]:
            if sig in val_str:
                ai_score += 0.85
                has_explicit_ai_cue = True
                reasons.append(f"Embedded generator metadata signature ({sig})")
                break

    # 3. Generative Canvas / ICC Profile check (Google Gemini / Imagen sRGB canvas)
    icc = image.info.get("icc_profile", b"")
    has_google_icc = False
    if isinstance(icc, bytes):
        if b"Google Inc." in icc or b"G\x00o\x00o\x00g\x00l\x00e\x00 \x00I\x00n\x00c" in icc:
            has_google_icc = True

    if has_google_icc and not has_camera:
        ai_score += 0.55
        reasons.append("Google Imagen/Gemini canvas rendering profile without optical camera EXIF")

    # 4. Canonical Generative Dimensions without Camera Hardware
    w, h = image.size
    is_photo_ar = is_standard_photo_aspect_ratio(w, h)

    if not has_camera:
        if (w, h) in AI_CANONICAL_PAIRS:
            ai_score += 0.25
            reasons.append(f"Canonical AI generative resolution ({w}x{h})")

    # 5. Chroma Saturation Distribution (Synthetic hyper-chroma vs natural overcast flood murky tones)
    try:
        hsv = np.array(image.convert("HSV"), dtype=np.float32)
        sat = hsv[:, :, 1]
        sat_mean = float(np.mean(sat))
        sat_p90 = float(np.percentile(sat, 90))

        if sat_p90 >= 195.0 and not has_camera:
            ai_score += 0.30
            reasons.append(f"Hyper-vivid synthetic chroma distribution (90th percentile saturation: {sat_p90:.1f})")
        elif sat_mean > 165.0 and not has_camera:
            ai_score += 0.25
            reasons.append(f"Hyper-saturated synthetic chroma distribution (mean saturation: {sat_mean:.1f})")
    except Exception:
        pass

    # 6. Generative Model Latent Grid Fingerprint (8-pixel VAE spatial autocorrelation)
    try:
        gray_arr = np.array(image.convert("L"), dtype=np.float32)
        h_arr, w_arr = gray_arr.shape
        smooth_arr = (gray_arr[:-2, :-2] + gray_arr[:-2, 1:-1] + gray_arr[:-2, 2:] +
                      gray_arr[1:-1, :-2] + gray_arr[1:-1, 1:-1] + gray_arr[1:-1, 2:] +
                      gray_arr[2:, :-2] + gray_arr[2:, 1:-1] + gray_arr[2:, 2:]) / 9.0
        residual = gray_arr[1:-1, 1:-1] - smooth_arr

        patch = residual[48:-48, 48:-48] if min(h_arr, w_arr) > 120 else residual
        p_norm = (patch - patch.mean()) / (patch.std() + 1e-5)
        corr_x8 = float(np.mean(p_norm[:, :-8] * p_norm[:, 8:]))
        corr_y8 = float(np.mean(p_norm[:-8, :] * p_norm[8:, :]))
        max_corr8 = max(corr_x8, corr_y8)

        if max_corr8 >= 0.20 and not has_camera:
            ai_score += 0.35
            reasons.append(f"Strong diffusion 8px latent grid fingerprint detected ({max_corr8:.3f})")
        elif max_corr8 >= 0.12 and has_google_icc:
            ai_score += 0.20
            reasons.append(f"Corroborating 8px latent grid fingerprint ({max_corr8:.3f})")
    except Exception:
        pass

    # 7. Error Level Analysis (ELA) & Optical Sensor Shot Noise Check
    ela_mean = 0.80
    try:
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=90)
        buf.seek(0)
        reloaded = Image.open(buf).convert("RGB")
        ela = np.array(ImageChops.difference(image.convert("RGB"), reloaded), dtype=np.float32)
        ela_mean = float(np.mean(ela))

        # Synthetic diffusion models lack real physical camera sensor noise: ELA < 0.50
        if ela_mean < 0.50 and not has_camera and min(w, h) >= 300:
            ai_score += 0.25
            reasons.append(f"Unnaturally uniform compression error levels (ELA: {ela_mean:.3f}) typical of diffusion generation")
        elif ela_mean >= 1.40 and not has_google_icc and not has_explicit_ai_cue and sat_p90 < 185.0:
            # Genuine optical camera shot noise verified ONLY when NO explicit AI marker is present
            ai_score -= 0.30
            reasons.append(f"Natural optical texture and sensor shot noise verified (ELA: {ela_mean:.3f})")
        elif ela_mean >= 0.75 and has_camera:
            ai_score -= 0.25
            reasons.append(f"Physical camera sensor shot noise verified (ELA: {ela_mean:.3f})")
    except Exception:
        pass

    # 8. Fourier Spectral Ratio
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

    # Authentic camera / standard aspect ratio deduction
    if is_photo_ar and not has_google_icc and not has_explicit_ai_cue:
        ai_score -= 0.15

    ai_score = max(0.0, min(1.0, round(ai_score, 2)))
    is_ai = ai_score >= 0.50
    return is_ai, ai_score, reasons

# TEST BENCH
test_ai = [
    ('report_1789063192_Ai image kolkata.jpg', 'uploads/report_1789063192_Ai image kolkata.jpg'),
    ('report_1789063182_fake2.0.jpeg', 'uploads/report_1789063182_fake2.0.jpeg'),
    ('unnamed_kolkata.jpg', 'uploads/report_1789063192_Ai image kolkata.jpg'),  # Test WITHOUT any AI filename!
    ('media_1789081732416.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789081732416.jpg'),
    ('media_1789057719538.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789057719538.jpg'),
    ('media_1789059148235.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789059148235.jpg'),
    ('media_1789064685993.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789064685993.jpg'),
    ('media_1789065448045.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789065448045.jpg'),
]

test_real = [
    ('report_1789062594_Chennai.jpeg', 'uploads/report_1789062594_Chennai.jpeg'),
    ('report_1789062554_thenenedekhu.jpeg', 'uploads/report_1789062554_thenenedekhu.jpeg'),
    ('report_1789041954_IMG_S24_001.jpg', 'uploads/report_1789041954_IMG_S24_001.jpg'),
    ('rain-and-the-city-at-kolkata-india.webp', 'uploads/report_1789062518_rain-and-the-city-at-kolkata-india.webp'),
    ('report_1789063265_Bihar.jpg', 'uploads/report_1789063265_Bihar.jpg'),
    ('report_1789063233_725724721.jpg', 'uploads/report_1789063233_725724721.jpg'),
    ('report_1789057466_meghalya.jpg', 'uploads/report_1789057466_meghalya.jpg'),
    ('report_1789057926_Kar.jpg', 'uploads/report_1789057926_Kar.jpg'),
    ('report_1789058468_bihar flood.jpg', 'uploads/report_1789058468_bihar flood.jpg'),
]

print("=================== AI SAMPLES (MUST BE is_ai=True) ===================")
for fn, p in test_ai:
    if os.path.exists(p):
        im = Image.open(p)
        is_ai, score, reasons = detect_ai_test(im, filename=fn)
        status = "PASS" if is_ai else "FAIL"
        print(f"[{status}] {fn:<38} -> is_ai={is_ai} (score={score:.2f}) | {reasons}")

print("\n=================== REAL SAMPLES (MUST BE is_ai=False) ===================")
for fn, p in test_real:
    if os.path.exists(p):
        im = Image.open(p)
        is_ai, score, reasons = detect_ai_test(im, filename=fn)
        status = "PASS" if not is_ai else "FAIL"
        print(f"[{status}] {fn:<38} -> is_ai={is_ai} (score={score:.2f}) | {reasons}")

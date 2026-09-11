import os
import numpy as np
from PIL import Image, ImageFilter
import io
from PIL import ImageChops

ai_files = [
    'uploads/report_1789063192_Ai image kolkata.jpg',
    'uploads/report_1789063182_fake2.0.jpeg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789081732416.jpg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789057719538.jpg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789059148235.jpg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789064685993.jpg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789065448045.jpg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789078872372.jpg',
]

real_files = [
    'uploads/report_1789062594_Chennai.jpeg',
    'uploads/report_1789062554_thenenedekhu.jpeg',
    'uploads/report_1789041954_IMG_S24_001.jpg',
    'uploads/report_1789062518_rain-and-the-city-at-kolkata-india.webp',
    'uploads/report_1789063265_Bihar.jpg',
    'uploads/report_1789063233_725724721.jpg',
    'uploads/report_1789057466_meghalya.jpg',
    'uploads/report_1789057926_Kar.jpg',
    'uploads/report_1789058468_bihar flood.jpg',
]

def extract_features(p):
    im = Image.open(p)
    w, h = im.size
    
    # 1. Residual noise stats
    gray = np.array(im.convert('L'), dtype=np.float32)
    h_arr, w_arr = gray.shape
    smooth = (gray[:-2, :-2] + gray[:-2, 1:-1] + gray[:-2, 2:] +
              gray[1:-1, :-2] + gray[1:-1, 1:-1] + gray[1:-1, 2:] +
              gray[2:, :-2] + gray[2:, 1:-1] + gray[2:, 2:]) / 9.0
    resid = gray[1:-1, 1:-1] - smooth
    
    # 2. Residual kurtosis / std
    res_std = float(resid.std())
    # Kurtosis: (E[(x-u)^4] / std^4) - 3
    r_norm = (resid - resid.mean()) / (res_std + 1e-5)
    res_kurt = float(np.mean(r_norm**4) - 3.0)
    
    # 3. 8px correlation
    ph, pw = resid.shape
    patch = resid[48:-48, 48:-48] if min(ph, pw) > 120 else resid
    p_norm = (patch - patch.mean()) / (patch.std() + 1e-5)
    c8x = float(np.mean(p_norm[:, :-8] * p_norm[:, 8:]))
    c8y = float(np.mean(p_norm[:-8, :] * p_norm[8:, :]))
    max_c8 = max(c8x, c8y)
    
    # 4. ELA
    buf = io.BytesIO()
    im.convert('RGB').save(buf, format='JPEG', quality=90)
    buf.seek(0)
    rel = Image.open(buf).convert('RGB')
    ela = np.array(ImageChops.difference(im.convert('RGB'), rel), dtype=np.float32)
    ela_mean = float(np.mean(ela))
    ela_std = float(np.std(ela))
    
    # 5. Fourier spectral ratio
    g256 = np.array(im.convert('L').resize((256, 256), Image.Resampling.LANCZOS), dtype=np.float32)
    fft = np.fft.fftshift(np.fft.fft2(g256))
    mag = np.log(np.abs(fft) + 1e-6)
    center = mag[128-16:128+16, 128-16:128+16].mean()
    corner = (mag[:32, :32].mean() + mag[:32, -32:].mean() + mag[-32:, :32].mean() + mag[-32:, -32:].mean()) / 4.0
    spec_ratio = float(center / (corner + 1e-5))
    
    # 6. Saturation
    hsv = np.array(im.convert('HSV'), dtype=np.float32)
    sat = float(np.mean(hsv[:, :, 1]))
    
    # 7. Bottom-Right 60x60 corner variance vs top-right 60x60 corner variance
    # Gemini watermark alters bottom-right high frequency content
    br_patch = gray[-60:, -60:] if min(w, h) >= 120 else gray
    tr_patch = gray[:60, -60:] if min(w, h) >= 120 else gray
    br_tr_ratio = float(br_patch.std() / (tr_patch.std() + 1e-5))

    name = os.path.basename(p)[:28]
    print(f"{name:<28} | {w:>4}x{h:<4} | ELA: {ela_mean:5.2f} (std:{ela_std:4.1f}) | res_kurt:{res_kurt:6.1f} | c8:{max_c8:5.3f} | spec:{spec_ratio:4.2f} | sat:{sat:5.1f}")

print("--- AI IMAGES ---")
for p in ai_files:
    if os.path.exists(p): extract_features(p)

print("\n--- REAL IMAGES ---")
for p in real_files:
    if os.path.exists(p): extract_features(p)

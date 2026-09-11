import os
import numpy as np
from PIL import Image
import io
from PIL import ImageChops

def analyze_details(path):
    im = Image.open(path)
    w, h = im.size
    # Check ICC
    icc = im.info.get('icc_profile', b'')
    has_google_icc = b'Google' in icc or b'G\x00o\x00o\x00g\x00l\x00e' in icc
    
    # Check Gemini / Imagen watermark in bottom right corner (30x30 to 120x120 area)
    # Most Imagen / Gemini images have a semi-transparent 4-pointed star or icon at bottom right
    # Let's check bottom-right 64x64 corner variance / characteristics
    br_crop = np.array(im.convert('L'))[-80:, -80:] if min(w, h) >= 120 else None
    
    # ELA
    buf = io.BytesIO()
    im.convert('RGB').save(buf, format='JPEG', quality=90)
    buf.seek(0)
    rel = Image.open(buf).convert('RGB')
    ela = np.array(ImageChops.difference(im.convert('RGB'), rel), dtype=np.float32)
    ela_mean = float(np.mean(ela))
    
    # Grid corr
    gray = np.array(im.convert('L'), dtype=np.float32)
    h_arr, w_arr = gray.shape
    smooth = (gray[:-2, :-2] + gray[:-2, 1:-1] + gray[:-2, 2:] +
              gray[1:-1, :-2] + gray[1:-1, 1:-1] + gray[1:-1, 2:] +
              gray[2:, :-2] + gray[2:, 1:-1] + gray[2:, 2:]) / 9.0
    resid = gray[1:-1, 1:-1] - smooth
    ph, pw = resid.shape
    patch = resid[48:-48, 48:-48] if min(ph, pw) > 120 else resid
    p_norm = (patch - patch.mean()) / (patch.std() + 1e-5)
    c8x = float(np.mean(p_norm[:, :-8] * p_norm[:, 8:]))
    c8y = float(np.mean(p_norm[:-8, :] * p_norm[8:, :]))
    
    # Spectral ratio
    g256 = np.array(im.convert('L').resize((256, 256), Image.Resampling.LANCZOS), dtype=np.float32)
    fft = np.fft.fftshift(np.fft.fft2(g256))
    mag = np.log(np.abs(fft) + 1e-6)
    center = mag[128-16:128+16, 128-16:128+16].mean()
    corner = (mag[:32, :32].mean() + mag[:32, -32:].mean() + mag[-32:, :32].mean() + mag[-32:, -32:].mean()) / 4.0
    spec_ratio = float(center / (corner + 1e-5))
    
    # Chroma saturation
    hsv = np.array(im.convert('HSV'), dtype=np.float32)
    sat = float(np.mean(hsv[:, :, 1]))
    
    print(f"{os.path.basename(path):<36} | size: {w:>4}x{h:<4} | ELA: {ela_mean:.3f} | c8: {max(c8x, c8y):.3f} | spec: {spec_ratio:.2f} | sat: {sat:>5.1f} | g_icc: {has_google_icc}")

print('--- REAL IMAGES ---')
real_list = [
    'uploads/report_1789062594_Chennai.jpeg',
    'uploads/report_1789041954_IMG_S24_001.jpg',
    'uploads/report_1789062518_rain-and-the-city-at-kolkata-india.webp',
    'uploads/report_1789062554_thenenedekhu.jpeg'
]
for p in real_list:
    if os.path.exists(p):
        analyze_details(p)

print('\n--- AI IMAGES (User uploaded in brain) ---')
folder = r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded'
for f in sorted(os.listdir(folder)):
    if f.endswith('.jpg'):
        analyze_details(os.path.join(folder, f))

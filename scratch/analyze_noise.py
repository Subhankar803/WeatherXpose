import glob
import os
from PIL import Image, ImageFilter, ImageChops
import numpy as np

files = sorted(glob.glob(r"C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\*.jpg"))

for p in files:
    name = os.path.basename(p)
    img = Image.open(p)
    w, h = img.size
    ar = round(w / h, 3)

    # 1. ELA mean
    import io
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=90)
    buf.seek(0)
    reloaded = Image.open(buf).convert("RGB")
    ela = np.array(ImageChops.difference(img.convert("RGB"), reloaded), dtype=np.float32)
    ela_mean = float(np.mean(ela))

    # 2. Camera sensor shot noise (Median filter residual)
    gray = np.array(img.convert("L"), dtype=np.float32)
    median = np.array(img.convert("L").filter(ImageFilter.MedianFilter(3)), dtype=np.float32)
    noise_residual = gray - median
    noise_std = float(np.std(noise_residual))

    # 3. High-frequency Laplacian variance (edge sharpness / sensor texture)
    laplacian_var = float(np.var(gray[1:, :] - gray[:-1, :]))

    # 4. Color saturation
    hsv = np.array(img.convert("HSV"), dtype=np.float32)
    sat_mean = float(np.mean(hsv[:, :, 1]))

    # 5. FFT spectral ratio
    g256 = np.array(img.convert("L").resize((256, 256), Image.Resampling.LANCZOS), dtype=np.float32)
    fft = np.fft.fftshift(np.fft.fft2(g256))
    mag = np.log(np.abs(fft) + 1e-6)
    center = mag[128-16:128+16, 128-16:128+16].mean()
    corner = (mag[:32, :32].mean() + mag[:32, -32:].mean() + mag[-32:, :32].mean() + mag[-32:, -32:].mean()) / 4.0
    spec_ratio = float(center / (corner + 1e-5))

    print(f"[{name}] {w}x{h} (AR:{ar}) | ELA:{ela_mean:.4f} | SensorNoiseStd:{noise_std:.2f} | LapVar:{laplacian_var:.1f} | SatMean:{sat_mean:.1f} | SpecRatio:{spec_ratio:.2f}")

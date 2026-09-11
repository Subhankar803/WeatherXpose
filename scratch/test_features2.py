import os
import numpy as np
from PIL import Image
from scipy.signal import convolve2d

ai_files = [
    'uploads/report_1789063192_Ai image kolkata.jpg',
    'uploads/report_1789063182_fake2.0.jpeg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789081732416.jpg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789057719538.jpg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789059148235.jpg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789064685993.jpg',
    r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789065448045.jpg',
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

def analyze(path):
    if not os.path.exists(path): return
    im = Image.open(path)
    w, h = im.size
    
    # Saturation
    hsv = np.array(im.convert('HSV'), dtype=np.float32)
    sat_mean = float(np.mean(hsv[:, :, 1]))
    sat_p90 = float(np.percentile(hsv[:, :, 1], 90))
    
    # High-pass
    gray = np.array(im.convert('L'), dtype=np.float32)
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    hp = convolve2d(gray, kernel, mode='valid')
    hp_std = float(hp.std())
    hp_kurt = float(np.mean(((hp - hp.mean()) / (hp_std + 1e-5))**4) - 3.0)
    
    rgb = np.array(im.convert('RGB'), dtype=np.float32)
    hp_r = convolve2d(rgb[:,:,0], kernel, mode='valid')
    hp_g = convolve2d(rgb[:,:,1], kernel, mode='valid')
    hp_b = convolve2d(rgb[:,:,2], kernel, mode='valid')
    rg_corr = float(np.corrcoef(hp_r.flatten(), hp_g.flatten())[0, 1])
    rb_corr = float(np.corrcoef(hp_r.flatten(), hp_b.flatten())[0, 1])
    
    name = os.path.basename(path)[:28]
    print(f"{name:<28} | sat_mean:{sat_mean:5.1f} | sat_p90:{sat_p90:5.1f} | hp_std:{hp_std:5.1f} | hp_kurt:{hp_kurt:5.1f} | rg_corr:{rg_corr:5.3f} | rb_corr:{rb_corr:5.3f}")

print("--- AI IMAGES ---")
for p in ai_files: analyze(p)

print("\n--- REAL IMAGES ---")
for p in real_files: analyze(p)

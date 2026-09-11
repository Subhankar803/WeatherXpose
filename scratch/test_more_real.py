import os
from PIL import Image
from scratch.test_ai_forensics import analyze_details

test_real_set = [
    'uploads/report_1789062594_Chennai.jpeg',
    'uploads/report_1789041954_IMG_S24_001.jpg',
    'uploads/report_1789062518_rain-and-the-city-at-kolkata-india.webp',
    'uploads/report_1789062554_thenenedekhu.jpeg',
    'uploads/report_1789057466_meghalya.jpg',
    'uploads/report_1789057926_Kar.jpg',
    'uploads/report_1789058468_bihar flood.jpg',
]

print("--- MORE REAL IMAGES ---")
for p in test_real_set:
    if os.path.exists(p):
        analyze_details(p)

import os
from app.services.image_forensics import analyze_image

test_cases = [
    # User's test AI images
    ('Ai image kolkata.jpg', 'uploads/report_1789063192_Ai image kolkata.jpg', True),
    ('fake2.0.jpeg', 'uploads/report_1789063182_fake2.0.jpeg', True),
    ('media_1789081732416.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789081732416.jpg', True),
    ('media_1789057719538.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789057719538.jpg', True),
    ('media_1789059148235.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789059148235.jpg', True),
    ('media_1789064685993.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789064685993.jpg', True),
    ('media_1789065448045.jpg', r'C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789065448045.jpg', True),
    
    # Real images (MUST BE FALSE)
    ('Chennai.jpeg', 'uploads/report_1789062594_Chennai.jpeg', False),
    ('thenenedekhu.jpeg', 'uploads/report_1789062554_thenenedekhu.jpeg', False),
    ('IMG_S24_001.jpg', 'uploads/report_1789041954_IMG_S24_001.jpg', False),
    ('rain-and-the-city...webp', 'uploads/report_1789062518_rain-and-the-city-at-kolkata-india.webp', False),
    ('Bihar.jpg', 'uploads/report_1789063265_Bihar.jpg', False),
    ('725724721.jpg', 'uploads/report_1789063233_725724721.jpg', False),
    ('meghalya.jpg', 'uploads/report_1789057466_meghalya.jpg', False),
    ('Kar.jpg', 'uploads/report_1789057926_Kar.jpg', False),
    ('bihar flood.jpg', 'uploads/report_1789058468_bihar flood.jpg', False),
]

all_passed = True
for name, p, expected in test_cases:
    if not os.path.exists(p):
        print(f"Skipping missing {p}")
        continue
    with open(p, 'rb') as f:
        data = f.read()
    res = analyze_image(data, filename=name)
    actual = res.get('is_ai_generated')
    score = res.get('ai_score', 0.0)
    reasons = res.get('ai_reason')
    passed = (actual == expected)
    if not passed: all_passed = False
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name:<26} (Exp:{expected}) -> is_ai={actual} (score={score:.2f}) | {reasons}")

print("\nFINAL OVERALL RESULT:", "ALL PASSED" if all_passed else "FAILURES DETECTED")

"""
Prepare the photo or illustration for clean ASCII conversion:
  1. remove the background (rembg with u2netp, or contour/color fallback) so the subject is isolated
  2. bilateral-smooth away noise/textures while keeping edges sharp
  3. stretch tones so background lands near pure white and features stay distinct
  4. darken line work (difference-of-gaussians ridges) for facial features, eyes, and hair contours
  5. composite onto white and crop square around the subject

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

    python scripts/prep_photo.py [input.png] [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

LINE_WEIGHT = 0.5

print(f"Reading {INP}...")
raw_img = Image.open(INP).convert("RGBA")

# 1. cut out subject
try:
    from rembg import remove, new_session
    sess = new_session("u2netp")
    cut = remove(raw_img, session=sess)
except Exception as e:
    print(f"rembg fallback ({e}), using luminance alpha mask...")
    rgb_arr = np.array(raw_img.convert("RGB"))
    gray_tmp = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2GRAY)
    mask_tmp = np.where(gray_tmp > 25, 255, 0).astype(np.uint8)
    cut = Image.fromarray(np.dstack([rgb_arr, mask_tmp]))

rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# 2. smooth texture, keep sharp edges
smooth = gray
for _ in range(3):
    smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

# 3. tone stretch over subject only
fg_indices = alpha > 100
if np.any(fg_indices):
    lo, hi = np.percentile(smooth[fg_indices], [5, 95])
    if hi <= lo:
        hi = lo + 1.0
    tone = np.clip((smooth.astype(np.float32) - lo) / (hi - lo), 0, 1)
else:
    tone = smooth.astype(np.float32) / 255.0

# 4. dark-on-light difference of gaussians
fine = cv2.GaussianBlur(smooth, (0, 0), 1.2).astype(np.float32)
coarse = cv2.GaussianBlur(smooth, (0, 0), 5.0).astype(np.float32)
lines = np.clip((coarse - fine) / 35.0, 0, 1)
out = np.clip(tone - LINE_WEIGHT * lines, 0, 1) * 255.0

# 5. paste onto white background with slight feathering
mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
out = out * mask + 255.0 * (1.0 - mask)

# 6. crop square around subject
ys, xs = np.where(alpha > 30)
if len(xs) > 0 and len(ys) > 0:
    side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 40
    cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
    canvas = np.full((side, side), 255, np.uint8)
    x0, y0 = cx - side // 2, cy - side // 2
    sx0, sy0 = max(x0, 0), max(y0, 0)
    sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
    canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)
else:
    canvas = out.astype(np.uint8)

os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
Image.fromarray(canvas, mode="L").save(OUT)
print(f"wrote {OUT}: {canvas.shape}")

"""
Convert a portrait photo into a clean, monochrome ASCII-art SVG (one light-gray color,
subject on a dark terminal background) that "types" itself in row by row, then holds.

Optimized for dark terminal backgrounds:
- Background and dark shadows/stripes map to blank space ' ' (terminal color #0d1117 shows through)
- Facial features, line art contours, glowing eyes, and highlights map to ASCII characters #c9d1d9
- SMIL left-to-right clip-wipe animation with typing cursor sweeps down from top to bottom
"""
import html
import os
import sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "kushal-ascii.svg")

COLS = int(os.environ.get("COLS", 140))
ART_W_TARGET = 800
CELL_W = ART_W_TARGET / COLS
CELL_H = CELL_W * 15 / 8
ROWS = round(COLS * 8 / 15)

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = 840
CANVAS_H = 880

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"

# timing: reveal once in ~5.8s
ROW_DUR = 5.8 / ROWS
STAGGER = ROW_DUR

if not os.path.exists(SRC):
    print(f"Error: {SRC} does not exist.", file=sys.stderr)
    sys.exit(1)

# Read image
img = cv2.imread(SRC)
if img is None:
    print(f"Error reading {SRC}", file=sys.stderr)
    sys.exit(1)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Bilateral smoothing: preserves sharp edges while removing grain
smooth = cv2.bilateralFilter(gray, 7, 45, 45)

# Difference of Gaussians edge detector for crisp manga/anime contours
g1 = cv2.GaussianBlur(smooth, (0, 0), 1.0).astype(np.float32)
g2 = cv2.GaussianBlur(smooth, (0, 0), 3.5).astype(np.float32)
edges = np.clip(np.abs(g1 - g2) * 4.2, 0, 255).astype(np.uint8)

# Highlights & face skin: zero out dark background (< 15)
hl = np.where(smooth > 15, smooth, 0).astype(np.float32)
hl_attenuated = np.clip(hl * 0.72, 0, 255).astype(np.uint8)

# Combine line art edges + highlights
combined = cv2.addWeighted(edges, 1.45, hl_attenuated, 0.75, 0)
combined = np.where(smooth > 15, combined, 0).astype(np.uint8)

# Resize to ASCII grid
small = cv2.resize(combined, (COLS, ROWS), interpolation=cv2.INTER_AREA)

# ASCII density ramp for dark background (sparse/empty -> bright dense)
RAMP = " .:-=+*cs#%@"

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        val = small[y, x]
        if val < 20:
            chars.append(" ")
        else:
            idx = int(val / 255.0 * (len(RAMP) - 1))
            idx = max(0, min(len(RAMP) - 1, idx))
            chars.append(RAMP[idx])
    rows_txt.append("".join(chars))

art_top = TITLEBAR_H + PAD * 0.35

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<defs>'
    f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
    f'</linearGradient></defs>',
    f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
             f'text-anchor="middle">kushal@github: ~$ ./portrait.sh</text>')

STATIC = bool(os.environ.get("STATIC"))
font_size = CELL_H * 0.86

for ry, line in enumerate(rows_txt):
    y = art_top + ry * CELL_H + CELL_H * 0.74
    row_y = art_top + ry * CELL_H
    delay = ry * STAGGER
    safe = html.escape(line)
    text = (f'<text xml:space="preserve" x="{PAD}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>')

    if STATIC:
        parts.append(text)
        continue

    parts.append(
        f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
    )
    parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    parts.append(
        f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{CURSOR}" opacity="0">'
        f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
    )

status_line_y = TITLEBAR_H + ART_H + PAD * 0.35
status_y = status_line_y + 19
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
             f'kushal@github:~$ whoami <tspan fill="{INK}">Kushal Lukhi</tspan></text>')
status_chars = len("kushal@github:~$ whoami Kushal Lukhi ")
parts.append(f'<rect x="{PAD + status_chars * 13 * 0.6:.1f}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" repeatCount="indefinite"/></rect>')

parts.append("</svg>")
svg = "".join(parts)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}: {CANVAS_W} x {CANVAS_H}, {len(svg)} bytes")

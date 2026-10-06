"""
Build a neofetch-style info card SVG to sit beside the ASCII portrait:
colored key/value rows for tech stack, focus areas, and project highlights.

Static content, hand-authored below. Lines fade and slide in on a short stagger.
STATIC=1 emits a frozen frame for static previews.
"""
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

# 840 x 880 canvas matches kushal-ascii.svg exactly so side-by-side columns have equal heights
W, H = 840, 880
PAD = 36
TITLEBAR_H = 40
KEY_X = PAD
VAL_X = PAD + 160
LINE_H = 36

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
KEY = "#ffa657"      # orange keys
SECTION = "#58a6ff"  # blue section headers
GREEN = "#3fb950"
ACCENT = "#22d3ee"

# Row structure:
# ("host",)
# ("kv", key, value)
# ("sec", title)
# ("bul", text)
# ("gap",)
ROWS = [
    ("host",),
    ("kv", "Role", "Software Engineer & AI Builder"),
    ("kv", "Focus", "Audio/Speech AI, Vision & Fullstack"),
    ("kv", "OS / Shell", "Windows · PowerShell · Linux"),
    ("gap",),
    ("sec", "Featured Projects"),
    ("bul", "dictly-whisper: AI speech-to-text dictation app"),
    ("bul", "gemini-watermark-remover: in-browser AI media tool"),
    ("gap",),
    ("sec", "Core Tech Stack"),
    ("kv", "Languages", "Python, TypeScript, JavaScript, SQL"),
    ("kv", "AI & ML", "Whisper, Faster-Whisper, ONNX, Gemini, OpenAI"),
    ("kv", "Fullstack", "React, Next.js, Node.js, FastAPI"),
    ("kv", "Tools", "Git, Docker, GitHub Actions, FFmpeg"),
    ("gap",),
    ("sec", "Highlights & Status"),
    ("bul", "Building fast, private open-source tools"),
    ("bul", "Automated GitHub profile refreshed via CI/CD"),
]


def esc(s):
    return html.escape(s)


def rise(inner, i):
    if STATIC:
        return f"<g>{inner}</g>"
    delay = 0.2 + i * 0.08
    return (f'<g opacity="0" transform="translate(0,6)">{inner}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.45s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 6" to="0 0" '
            f'begin="{delay:.2f}s" dur="0.45s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/></g>')


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<defs>'
    f'<linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#ibg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}" stroke-width="1"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*20}" cy="{TITLEBAR_H/2}" r="6" fill="{dotcol}"/>')
parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 5}" fill="{MUTED}" font-size="14" '
             f'text-anchor="middle">kushal@github: ~$ neofetch</text>')

y = TITLEBAR_H + 46
for i, row in enumerate(ROWS):
    kind = row[0]
    if kind == "gap":
        y += LINE_H * 0.55
        continue
    if kind == "host":
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" font-size="20" font-weight="700">'
                 f'<tspan fill="{GREEN}">kushal</tspan><tspan fill="{MUTED}">@</tspan>'
                 f'<tspan fill="{ACCENT}">github</tspan></text>'
                 f'<line x1="{KEY_X+170}" y1="{y-6:.1f}" x2="{W-PAD}" y2="{y-6:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "sec":
        title = esc(row[1])
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{SECTION}" font-size="17" font-weight="700">'
                 f'&#8212; {title}</text>'
                 f'<line x1="{KEY_X + 20 + len(row[1])*11}" y1="{y-6:.1f}" x2="{W-PAD}" y2="{y-6:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "kv":
        key, val = esc(row[1]), esc(row[2])
        inner = (f'<text x="{KEY_X}" y="{y:.1f}" fill="{KEY}" font-size="17" font-weight="700">{key}</text>'
                 f'<text x="{VAL_X}" y="{y:.1f}" fill="{INK}" font-size="17">{val}</text>')
    elif kind == "bul":
        txt = esc(row[1])
        inner = (f'<circle cx="{KEY_X+6}" cy="{y-5:.1f}" r="3.5" fill="{GREEN}"/>'
                 f'<text x="{KEY_X+20}" y="{y:.1f}" fill="{INK}" font-size="17">{txt}</text>')
    else:
        continue
    parts.append(rise(inner, i))
    y += LINE_H

parts.append("</svg>")
svg = "".join(parts)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}: {W} x {H}, {len(svg)} bytes")

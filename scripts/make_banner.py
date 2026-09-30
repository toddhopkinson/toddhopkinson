"""Build the animated Lava Monster wordmark banner for the GitHub profile README.

Block capitals (IBM Plex Sans Bold, as outlines), the purple eye in the O
(blinks and glances around), the pixel lava pool (a seamless loop of the
site's pool), and a drip falling from the pool's left end. Pure SVG + CSS
animation, so GitHub shows it animated with no JavaScript.
"""
import io, math, random, sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

FONT = sys.argv[1]
OUT = sys.argv[2]

INK, GROUND, RULE = '#F2EDE6', '#0C0B0A', '#2A2623'
K = dict(yellow='y', orange='o', hot='h', ember='e', dark='d', deep='p', white='w')   # short CSS classes
P = dict(deep='#3a0e02', dark='#6e1d04', ember='#a8390a', hot='#d9530c',
         orange='#f07c16', yellow='#ffbd2e', white='#fff3b0')

FS = 96                      # font size in SVG units
TRACK = 0.08 * FS            # letter-spacing, as on the site
TEXT = 'LAVA MONSTER'
W, H = 1200, 236
BASE_Y = 118                 # baseline

# ---- Shape the text with HarfBuzz (kerning) and draw glyph outlines -------
tt = TTFont(FONT)
data = io.BytesIO(); tt.flavor = None; tt.save(data)
blob = hb.Blob(data.getvalue()); face = hb.Face(blob); font = hb.Font(face)
upem = tt['head'].unitsPerEm
buf = hb.Buffer(); buf.add_str(TEXT); buf.guess_segment_properties()
hb.shape(font, buf, {'kern': True, 'liga': False})
glyph_order = tt.getGlyphOrder(); gs = tt.getGlyphSet()
scale = FS / upem

pens, x, o_box, total = [], 0.0, None, 0.0
for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
    name = glyph_order[info.codepoint]
    ch = TEXT[info.cluster]
    gx = x + pos.x_offset * scale
    if ch.strip():
        bp = BoundsPen(gs); gs[name].draw(bp)
        xmin, ymin, xmax, ymax = bp.bounds
        if ch == 'O':
            o_box = (gx + xmin * scale, -ymax * scale, gx + xmax * scale, -ymin * scale)
        else:
            sp = SVGPathPen(gs)
            gs[name].draw(TransformPen(sp, (scale, 0, 0, -scale, gx, 0)))
            pens.append(sp.getCommands())
    x += pos.x_advance * scale + TRACK
total = x - TRACK                      # the site's pool is 100% - one letter-space wide
OX = (W - total) / 2                   # centre the name

# ---- The pool: a seamless loop of lava-pool.js ----------------------------
PX = 6.4                               # 2 CSS px at 30px font, scaled to 96
COLS = int(total / PX)
ROWS = 7
N = 32                                 # frames; 12 fps -> 2.67 s loop
FPS = 12
W1 = 2 * math.pi * 2 / N               # surface speeds that wrap exactly in N frames
W2 = -2 * math.pi * 1 / N

def surface(xc, t):
    w = math.sin(xc * 0.42 + t * W1) * 0.9 + math.sin(xc * 0.17 + t * W2) * 0.7
    s = 3 - round(w)
    if xc < 2 or xc > COLS - 3: s += 1
    if xc in (0, COLS - 1): s += 1
    return min(s, ROWS - 2)

random.seed(7)
bubbles, drops = [], []
def step(t):
    global bubbles, drops
    if len(bubbles) < max(2, COLS / 10) and random.random() < 0.3:
        bubbles.append(dict(x=2 + random.randrange(COLS - 4), y=ROWS - 1, big=random.random() < 0.3))
    for b in bubbles:
        if random.random() < 0.6: b['y'] -= 1
    keep = []
    for b in bubbles:
        top = surface(b['x'], t)
        if b['y'] > top: keep.append(b); continue
        n = 3 if b['big'] else 1
        for i in range(n):
            drops.append(dict(x=b['x'], y=top - 1, vx=0 if n == 1 else i - 1, vy=-2 if b['big'] else -1, age=0))
    bubbles = keep
    for d in drops:
        d['age'] += 1
        if d['age'] == 1: d['x'] += d['vx']
        d['y'] += d['vy']; d['vy'] += 1
    drops = [d for d in drops if 0 <= d['y'] < surface(max(0, min(COLS - 1, d['x'])), t)]

def frame(t):
    px = {}
    for xc in range(COLS):
        top = surface(xc, t)
        for y in range(top, ROWS):
            d = y - top
            if d == 0: c = 'yellow' if top <= 2 else 'orange'
            elif d == 1: c = 'hot'
            elif y == ROWS - 1: c = 'deep'
            else: c = 'hot' if (xc * 5 + y * 3 + (t // 4) % 8) % 11 == 0 else ('ember' if d == 2 else 'dark')
            if d == 0 and (xc + t) % 16 == 0: c = 'white'
            px[(xc, y)] = c
    for b in bubbles:
        if b['y'] <= surface(b['x'], t): continue
        px[(b['x'], b['y'])] = 'yellow'
        if b['big'] and b['x'] + 1 < COLS: px[(b['x'] + 1, b['y'])] = 'orange'
    for d in drops:
        if 0 <= d['x'] < COLS: px[(d['x'], d['y'])] = 'white' if d['age'] < 2 else 'yellow'
    return px

for t in range(-3 * N, 0): step(t)     # warm up so bubbles are already rising
frames = []
for t in range(N):
    step(t); frames.append(frame(t))

# Pixels that never change go in one static layer; each frame draws the rest
static = {k: v for k, v in frames[0].items() if all(f.get(k) == v for f in frames)}
def runs(px):
    out = []
    for y in range(ROWS):
        xc = 0
        while xc < COLS:
            c = px.get((xc, y))
            if c is None: xc += 1; continue
            x0 = xc
            while xc < COLS and px.get((xc, y)) == c: xc += 1
            out.append((x0, y, xc - x0, c))
    return out
def rects(rs):
    return ''.join(f'<rect class="{K[c]}" x="{x}" y="{y}" width="{w}" height="1"/>' for x, y, w, c in rs)

POOL_Y = BASE_Y + 0.2 * FS             # pool top: just under the line box, as on the site
pool_static = rects(runs(static))
pool_frames = ''.join(
    f'<g class="f" style="animation-delay:{-(N - i) * 1.0 / FPS:.4f}s">'
    + rects(runs({k: v for k, v in f.items() if static.get(k) != v})) + '</g>'
    for i, f in enumerate(frames))

# ---- The eye in the O ------------------------------------------------------
ox0, oy0, ox1, oy1 = o_box
cx, cy = OX + (ox0 + ox1) / 2, BASE_Y + (oy0 + oy1) / 2
rx, ry = (ox1 - ox0) / 2, (oy1 - oy0) / 2
ring = FS * 0.055
ex, ey = rx - ring / 2, ry - ring / 2
ir, pr = min(ex, ey) * 0.667, min(ex, ey) * 0.2935
reach_x, reach_y = ex - ir * 0.92, ey - ir * 0.92
# The site's idle glance: five positions, 1.6 s each (8 s loop)
LOOK = [(0, 0), (-0.8, 0.1), (0.7, -0.2), (0.2, 0.7), (-0.3, 0.4)]
# hold each position, then move over ~0.3 s
glance = []
for i, (lx, ly) in enumerate(LOOK):
    a, b = i * 20, i * 20 + 16
    glance.append(f'{a + 4 if i else 0}%,{b}% {{transform:translate({lx * reach_x:.2f}px,{ly * reach_y:.2f}px)}}')
glance.append(f'100% {{transform:translate(0px,0px)}}')

# ---- The drip: a bead swells under the pool's left lip, drops and fades ----
DRIP_X = OX - PX * 2.5
LIP_Y = POOL_Y + PX * 6

css = f'''
{''.join(f'.{K[k]}{{fill:{v}}}' for k, v in P.items())}
.f{{opacity:0;animation:fr {N / FPS:.4f}s step-end infinite}}
@keyframes fr{{0%{{opacity:1}}{100 / N:.4f}%,100%{{opacity:0}}}}
.iris{{animation:glance 8s ease-in-out infinite}}
@keyframes glance{{{''.join(glance)}}}
.lid{{transform-box:fill-box;animation:blink 5.3s linear infinite}}
.lid.t{{transform-origin:50% 0}}.lid.b{{transform-origin:50% 100%}}
@keyframes blink{{0%,58%,62.6%,100%{{transform:scaleY(0)}}60.3%{{transform:scaleY(1)}}}}
.bead{{transform-box:fill-box;transform-origin:50% 0;animation:bead 4s ease-in infinite}}
@keyframes bead{{0%{{transform:translateY(0) scale(0.2);opacity:1}}55%{{transform:translateY(4px) scale(1);opacity:1}}
56%{{transform:translateY(6px) scale(1);opacity:1}}88%{{transform:translateY(70px) scale(1);opacity:0}}100%{{transform:translateY(70px) scale(0.2);opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.f,.iris,.lid,.bead{{animation:none}}.f:first-of-type{{opacity:1}}}}
'''

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Lava Monster">
<title>Lava Monster</title>
<defs>
<radialGradient id="sclera" cx="{cx - ex * 0.25:.2f}" cy="{cy - ey * 0.3:.2f}" r="{max(ex, ey):.2f}" gradientUnits="userSpaceOnUse">
<stop offset="0" stop-color="#fffaf2"/><stop offset="0.7" stop-color="#f1e7da"/><stop offset="1" stop-color="#d9c9b6"/></radialGradient>
<radialGradient id="irisg" cx="0.5" cy="0.5" r="0.5" fx="0.5" fy="0.5">
<stop offset="0.15" stop-color="#c4a6ff"/><stop offset="0.6" stop-color="#8b5cf6"/><stop offset="1" stop-color="#4c1d95"/></radialGradient>
<clipPath id="ball"><ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{ex:.2f}" ry="{ey:.2f}"/></clipPath>
</defs>
<style>{css}</style>
<rect width="{W}" height="{H}" rx="18" fill="{GROUND}"/>
<g fill="{INK}" transform="translate({OX:.2f} {BASE_Y})">{''.join(f'<path d="{d}"/>' for d in pens)}</g>
<g clip-path="url(#ball)">
<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{ex:.2f}" ry="{ey:.2f}" fill="url(#sclera)"/>
<g class="iris"><circle cx="{cx:.2f}" cy="{cy:.2f}" r="{ir:.2f}" fill="url(#irisg)" stroke="#2e1065" stroke-width="{max(0.75, ir * 0.08):.2f}"/>
<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{pr:.2f}" fill="#0b0612"/>
<circle cx="{cx - ir * 0.28:.2f}" cy="{cy - ir * 0.32:.2f}" r="{max(0.8, ir * 0.16):.2f}" fill="#fff" fill-opacity="0.92"/></g>
<rect class="lid t" x="{cx - ex:.2f}" y="{cy - ey - 1:.2f}" width="{ex * 2:.2f}" height="{ey + 1.5:.2f}" fill="#3a1208"/>
<rect class="lid b" x="{cx - ex:.2f}" y="{cy - 0.5:.2f}" width="{ex * 2:.2f}" height="{ey + 1.5:.2f}" fill="#3a1208"/>
</g>
<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx - ring / 2:.2f}" ry="{ry - ring / 2:.2f}" fill="none" stroke="{INK}" stroke-width="{ring:.2f}"/>
<g transform="translate({OX:.2f} {POOL_Y:.2f}) scale({PX})" shape-rendering="crispEdges">{pool_static}{pool_frames}</g>
<g shape-rendering="crispEdges">
<rect class="h" x="{OX - PX:.2f}" y="{LIP_Y - PX:.2f}" width="{PX:.2f}" height="{PX:.2f}"/>
<rect class="o" x="{DRIP_X:.2f}" y="{LIP_Y - PX:.2f}" width="{PX * 1.5:.2f}" height="{PX:.2f}"/>
<g class="bead"><rect class="o" x="{DRIP_X:.2f}" y="{LIP_Y:.2f}" width="{PX * 1.5:.2f}" height="{PX:.2f}"/>
<rect class="y" x="{DRIP_X + PX * 0.5:.2f}" y="{LIP_Y:.2f}" width="{PX:.2f}" height="{PX * 0.6:.2f}"/>
<rect class="h" x="{DRIP_X:.2f}" y="{LIP_Y + PX:.2f}" width="{PX * 1.5:.2f}" height="{PX * 0.8:.2f}"/></g>
</g>
</svg>'''
open(OUT, 'w').write(svg)
print(f'cols={COLS} frames={N} bytes={len(svg)} total={total:.1f} o_box={o_box}')

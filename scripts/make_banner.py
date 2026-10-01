"""Build the animated Lava Monster wordmark banner for the GitHub profile README.

The site's wordmark (Archivo 900, outlined, from lavamonster.io's components/Wordmark.astro)
on the site's indigo ground, with a red eye in the O that glances around and blinks the
way the site's eye does (lib/wordmark-eye.js). No lava. Pure SVG + CSS animation, so
GitHub shows it animated with no JavaScript.

    python3 scripts/make_banner.py <lavamonster-io repo>/src/components/Wordmark.astro assets/lava-monster.svg
"""
import re, sys

SRC, OUT = sys.argv[1], sys.argv[2]

GROUND, INK = '#141A33', '#EEF0FA'                                      # site tokens: --ground, --ink
IRIS = dict(centre='#fca5a5', middle='#ef4444', edge='#991b1b', rim='#450a0a')   # the site's red iris
W, H = 1200, 200
WM_W = 1000                                                             # the name's width in the banner

# ---- The wordmark, straight from the site's SVG ------------------------------
astro = open(SRC).read()
vx, vy, vw, vh = map(float, re.search(r'viewBox="([^"]+)"', astro).group(1).split())
fx, fy, fw, fh = map(float, re.search(r'data-o="([^"]+)"', astro).group(1).split(','))
paths = re.findall(r'<path( class="wordmark-o")? d="([^"]+)"', astro)
letters = [d for cls, d in paths if not cls]                            # every letter but the O

s = WM_W / vw
OX, OY = (W - vw * s) / 2, (H - vh * s) / 2

# ---- The eye, sized as wordmark-eye.js sizes it ------------------------------
ow, oh = vw * s * fw, vh * s * fh
cx, cy = OX + vw * s * fx + ow / 2, OY + vh * s * fy + oh / 2
rx, ry = ow / 2, oh / 2
ring = max(1, oh * 55 / 712)                                            # the O's ink ring
ex, ey = rx - ring / 2, ry - ring / 2                                   # eyeball inside the ring
ir, pr = min(ex, ey) * 0.667, min(ex, ey) * 0.2935                      # iris, pupil
reach_x, reach_y = ex - ir * 0.92, ey - ir * 0.92

# The site's idle glance: five positions, 1.6 s each (8 s loop), easing between them
LOOK = [(0, 0), (-0.8, 0.1), (0.7, -0.2), (0.2, 0.7), (-0.3, 0.4)]
glance = []
for i, (lx, ly) in enumerate(LOOK):
    a, b = i * 20, i * 20 + 16
    glance.append(f'{a + 4 if i else 0}%,{b}%{{transform:translate({lx * reach_x:.2f}px,{ly * reach_y:.2f}px)}}')
glance.append('100%{transform:translate(0px,0px)}')

css = f'''
.iris{{animation:glance 8s ease-in-out infinite}}
@keyframes glance{{{''.join(glance)}}}
.lid{{transform-box:fill-box;animation:blink 5.3s linear infinite}}
.lid.t{{transform-origin:50% 0}}.lid.b{{transform-origin:50% 100%}}
@keyframes blink{{0%,58%,62.6%,100%{{transform:scaleY(0)}}60.3%{{transform:scaleY(1)}}}}
@media (prefers-reduced-motion:reduce){{.iris,.lid{{animation:none}}}}
'''

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Lava Monster">
<title>Lava Monster</title>
<defs>
<radialGradient id="sclera" cx="{cx - ex * 0.25:.2f}" cy="{cy - ey * 0.3:.2f}" r="{max(ex, ey):.2f}" gradientUnits="userSpaceOnUse">
<stop offset="0" stop-color="#fffaf2"/><stop offset="0.7" stop-color="#f1e7da"/><stop offset="1" stop-color="#d9c9b6"/></radialGradient>
<radialGradient id="irisg" cx="0.5" cy="0.5" r="0.5">
<stop offset="0.15" stop-color="{IRIS['centre']}"/><stop offset="0.55" stop-color="{IRIS['middle']}"/><stop offset="1" stop-color="{IRIS['edge']}"/></radialGradient>
<clipPath id="ball"><ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{ex:.2f}" ry="{ey:.2f}"/></clipPath>
</defs>
<style>{css}</style>
<rect width="{W}" height="{H}" rx="18" fill="{GROUND}"/>
<g fill="{INK}" transform="translate({OX:.2f} {OY:.2f}) scale({s:.6f}) translate({-vx:g} {-vy:g})">{''.join(f'<path d="{d}"/>' for d in letters)}</g>
<g clip-path="url(#ball)">
<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{ex:.2f}" ry="{ey:.2f}" fill="url(#sclera)"/>
<g class="iris"><circle cx="{cx:.2f}" cy="{cy:.2f}" r="{ir:.2f}" fill="url(#irisg)" stroke="{IRIS['rim']}" stroke-width="{max(0.75, ir * 0.08):.2f}"/>
<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{pr:.2f}" fill="#0b0612"/>
<circle cx="{cx - ir * 0.28:.2f}" cy="{cy - ir * 0.32:.2f}" r="{max(0.8, ir * 0.16):.2f}" fill="#fff" fill-opacity="0.92"/></g>
<rect class="lid t" x="{cx - ex:.2f}" y="{cy - ey - 1:.2f}" width="{ex * 2:.2f}" height="{ey + 1.5:.2f}" fill="#3a1208"/>
<rect class="lid b" x="{cx - ex:.2f}" y="{cy - 0.5:.2f}" width="{ex * 2:.2f}" height="{ey + 1.5:.2f}" fill="#3a1208"/>
</g>
<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{ex:.2f}" ry="{ey:.2f}" fill="none" stroke="{INK}" stroke-width="{ring:.2f}"/>
</svg>'''
open(OUT, 'w').write(svg)
print(f'letters={len(letters)} bytes={len(svg)} eye=({cx:.1f},{cy:.1f}) r=({rx:.1f},{ry:.1f})')

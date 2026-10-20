"""Generate every SVG on the Lecrupus profile README.

    python tools/gen_assets.py            # uses GITHUB_TOKEN if set, else unauthenticated API
    python tools/gen_assets.py --offline  # skip the API, use the fallback numbers below

All art is drawn here in raw SVG: no images, no external fonts, no third-party widgets.
The inventory panel (language essence) is the only part that reads live data; the
daily workflow in .github/workflows/refresh.yml reruns this script to keep it current.
"""

import json
import math
import os
import random
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USER = "Lecrupus"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
W = 1200

# ── palette ──────────────────────────────────────────────────────────────────
ABYSS = "#04060c"
DEEP = "#080d1a"
STONE = "#0e1527"
SLATE = "#17213a"
INK = "#2a3858"
MIST = "#8a9bb8"
BONE = "#e9eef6"
SOUL = "#a6ecff"
LANTERN = "#f4c76e"
EMBER = "#ff9a52"
MOSS = "#79c99b"
VIOLET = "#9d8cf0"

SERIF = "'Cinzel','Trajan Pro','Palatino Linotype','Book Antiqua',Palatino,Georgia,serif"
BODY = "'Palatino Linotype','Book Antiqua',Palatino,Georgia,serif"
ITALIC = 'font-style="italic"'

# Fallback for --offline / API failure (bytes, measured 2026-10-20, notebooks + markup excluded).
FALLBACK_LANGS = {"Python": 432350, "JavaScript": 244953, "Go": 92392, "C++": 58222,
                  "Dockerfile": 9011, "Shell": 5978}
FALLBACK_REPOS = 26
SKIP_LANGS = {"Jupyter Notebook", "HTML", "CSS", "Batchfile", "PowerShell", "Makefile"}


# ── helpers ──────────────────────────────────────────────────────────────────
def svg(width, height, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title>{body}</svg>\n')


def write(name, content):
    (ASSETS / name).write_text(content, encoding="utf-8")
    print(f"  wrote assets/{name}  ({len(content) // 1024} KB)")


def t(x, y, s, size, fill=BONE, family=SERIF, anchor="middle", weight="400", spacing=0,
      extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" letter-spacing="{spacing}" '
            f'{extra}>{escape(s)}</text>')


def defs_common():
    return f"""
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="3" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="bigglow" x="-100%" y="-100%" width="300%" height="300%">
  <feGaussianBlur stdDeviation="9"/>
</filter>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="7" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 .6  0 0 0 0 .7  0 0 0 0 .9  0 0 0 .05 0"/>
</filter>
<radialGradient id="lanternlight"><stop offset="0" stop-color="{LANTERN}" stop-opacity=".55"/>
  <stop offset="1" stop-color="{LANTERN}" stop-opacity="0"/></radialGradient>
<radialGradient id="soullight"><stop offset="0" stop-color="{SOUL}" stop-opacity=".5"/>
  <stop offset="1" stop-color="{SOUL}" stop-opacity="0"/></radialGradient>
"""


def css_common():
    return """
@keyframes rise1{0%{transform:translate(0,0);opacity:0}15%{opacity:.9}100%{transform:translate(18px,-260px);opacity:0}}
@keyframes rise2{0%{transform:translate(0,0);opacity:0}20%{opacity:.7}100%{transform:translate(-22px,-300px);opacity:0}}
@keyframes rise3{0%{transform:translate(0,0);opacity:0}10%{opacity:.8}100%{transform:translate(6px,-220px);opacity:0}}
@keyframes flicker{0%,100%{opacity:.85}12%{opacity:.6}20%{opacity:.95}48%{opacity:.7}60%{opacity:1}80%{opacity:.75}}
@keyframes sway{0%,100%{transform:rotate(-3deg)}50%{transform:rotate(3deg)}}
@keyframes pulse{0%,100%{opacity:.35;transform:scale(.85)}50%{opacity:1;transform:scale(1.15)}}
@keyframes blink{0%,45%{opacity:1}50%,95%{opacity:.15}100%{opacity:1}}
@keyframes eyes{0%,92%,100%{transform:scaleY(1)}95%{transform:scaleY(.1)}}
@keyframes drift{0%{transform:translateX(0)}100%{transform:translateX(-1200px)}}
.fl{animation:flicker 3.2s infinite}
.sw{transform-box:fill-box;transform-origin:50% 0;animation:sway 6s ease-in-out infinite}
.pu{transform-box:fill-box;transform-origin:center;animation:pulse 2.8s ease-in-out infinite}
.bl{animation:blink 2.4s infinite}
.ey{transform-box:fill-box;transform-origin:center;animation:eyes 5s infinite}
"""


def spores(n, x0, x1, y0, y1, seed, colors=(SOUL, SOUL, BONE, LANTERN)):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        r = rnd.choice((1, 1.2, 1.5, 1.8, 2.4))
        dur = rnd.uniform(7, 16)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{rnd.choice(colors)}" '
                   f'filter="url(#glow)" style="animation:rise{rnd.randint(1, 3)} {dur:.1f}s '
                   f'linear {-rnd.uniform(0, dur):.1f}s infinite"/>')
    return "".join(out)


def jagged(width, base, amp, step, seed, top):
    """Stalactite (top=True) or rock-floor silhouette as a closed path."""
    rnd = random.Random(seed)
    edge = 0 if top else 9999
    pts, x = [], 0
    while x <= width + step:
        spike = rnd.random() < .22
        d = rnd.uniform(.2, 1) * amp * (2.4 if spike else 1)
        y = base + d if top else base - d
        if spike and top:
            pts += [(x - step * .25, base + amp * .3), (x, y), (x + step * .25, base + amp * .3)]
        else:
            pts.append((x, y))
        x += step * rnd.uniform(.6, 1.4)
    edge = 0 if top else 2000
    path = f"M0,{edge} " + " ".join(f"L{px:.0f},{py:.0f}" for px, py in pts)
    return path + f" L{width},{edge} Z"


def blob(cx, cy, rx, ry, seed, n=11):
    """Irregular closed region (Catmull-Rom smoothed) for the map."""
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        k = rnd.uniform(.78, 1.12)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d + "Z"


def flourish(cx, cy, half, color=MIST, title=None):
    """Ornate horizontal divider: fading rules, curls and a centre diamond."""
    g = f"""
<linearGradient id="fadeL{cy}" x1="1" x2="0"><stop offset="0" stop-color="{color}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>
<linearGradient id="fadeR{cy}" x1="0" x2="1"><stop offset="0" stop-color="{color}"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>"""
    gap = 26 if title is None else len(title) * 13 + 70
    out = f"<defs>{g}</defs>"
    out += (f'<path d="M{cx - gap},{cy} L{cx - half},{cy}" stroke="url(#fadeL{cy})" stroke-width="1.2"/>'
            f'<path d="M{cx + gap},{cy} L{cx + half},{cy}" stroke="url(#fadeR{cy})" stroke-width="1.2"/>')
    for s in (-1, 1):
        x = cx + s * gap
        out += (f'<path d="M{x},{cy} c{s * 18},-14 {s * 40},-10 {s * 46},0 '
                f'c{s * 4},8 {s * -8},12 {s * -14},6" fill="none" stroke="{color}" stroke-width="1.2"/>'
                f'<path d="M{x},{cy} c{s * 18},14 {s * 40},10 {s * 46},0" fill="none" stroke="{color}" '
                f'stroke-width="1.2" opacity=".6"/>'
                f'<circle cx="{x + s * 74}" cy="{cy}" r="2" fill="{color}"/>')
    if title is None:
        out += (f'<path d="M{cx},{cy - 9} L{cx + 9},{cy} L{cx},{cy + 9} L{cx - 9},{cy} Z" fill="none" '
                f'stroke="{BONE}" stroke-width="1.3"/><circle cx="{cx}" cy="{cy}" r="2.4" fill="{SOUL}" '
                f'filter="url(#glow)" class="pu"/>')
    else:
        out += t(cx, cy + 9, title, 26, BONE, SERIF, spacing=8, weight="600")
    return out


def wanderer(x, y, s=1.0):
    """Original hooded lantern-bearer (not any existing game character)."""
    return f"""
<g transform="translate({x},{y}) scale({s})">
  <circle cx="26" cy="-46" r="70" fill="url(#lanternlight)" class="fl"/>
  <path d="M0,-40 C-15,-37 -21,-8 -23,20 L-28,31 L-8,27 L0,32 L9,27 L28,31 L23,20 C21,-8 15,-37 0,-40 Z" fill="#0b1122" stroke="{INK}" stroke-width="1.2"/>
  <path d="M-14,-27 C-15,-52 15,-52 14,-27 C13,-15 -13,-15 -14,-27 Z" fill="#111a31" stroke="{INK}" stroke-width="1.2"/>
  <ellipse cx="0" cy="-26" rx="8.5" ry="7.5" fill="#010208"/>
  <g class="ey"><ellipse cx="-3.6" cy="-27" rx="1.7" ry="2.3" fill="{SOUL}" filter="url(#glow)"/>
  <ellipse cx="3.6" cy="-27" rx="1.7" ry="2.3" fill="{SOUL}" filter="url(#glow)"/></g>
  <line x1="17" y1="31" x2="23" y2="-56" stroke="#4a3a2a" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M23,-56 q8,-2 9,6" fill="none" stroke="#4a3a2a" stroke-width="2"/>
  <g class="sw" style="transform-origin:32px -50px">
    <line x1="32" y1="-50" x2="32" y2="-44" stroke="{MIST}" stroke-width="1"/>
    <path d="M27,-44 h10 l-1.5,12 h-7 Z" fill="{LANTERN}" opacity=".9" class="fl" filter="url(#glow)"/>
    <path d="M26,-44 h12 M27,-32 h10" stroke="#5b4630" stroke-width="1.6"/>
  </g>
</g>"""


def vine(x, length, seed, bulb=True):
    rnd = random.Random(seed)
    pts, y = [], 0
    d = f"M{x},0"
    while y < length:
        y2 = min(length, y + rnd.uniform(18, 30))
        d += f" Q{x + rnd.uniform(-8, 8):.0f},{(y + y2) / 2:.0f} {x + rnd.uniform(-3, 3):.0f},{y2:.0f}"
        y = y2
    out = (f'<g class="sw" style="animation-duration:{rnd.uniform(5, 9):.1f}s;'
           f'animation-delay:-{rnd.uniform(0, 5):.1f}s">'
           f'<path d="{d}" fill="none" stroke="#1d2a47" stroke-width="2"/>')
    if bulb:
        out += (f'<circle cx="{x}" cy="{length + 6}" r="16" fill="url(#soullight)" class="fl"/>'
                f'<circle cx="{x}" cy="{length + 6}" r="4" fill="{SOUL}" filter="url(#glow)"/>')
    return out + "</g>"


# ── live data ────────────────────────────────────────────────────────────────
def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}",
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": "lecrupus-profile"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fetch_stats(offline):
    if offline:
        return FALLBACK_LANGS, FALLBACK_REPOS
    try:
        repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
        langs = {}
        for r in repos:
            for k, v in api(f"/repos/{USER}/{r['name']}/languages").items():
                if k not in SKIP_LANGS:
                    langs[k] = langs.get(k, 0) + v
        return langs, len(repos)
    except Exception as e:  # keep the README rendering even if the API hiccups
        print(f"  API unavailable ({e}); using fallback numbers")
        return FALLBACK_LANGS, FALLBACK_REPOS


# ── panels ───────────────────────────────────────────────────────────────────
def hero():
    H = 480
    rnd = random.Random(3)
    body = f"<defs>{defs_common()}"
    body += f"""
<radialGradient id="sky" cx=".5" cy=".35" r=".75"><stop offset="0" stop-color="#16233f"/>
  <stop offset=".55" stop-color="{DEEP}"/><stop offset="1" stop-color="{ABYSS}"/></radialGradient>
<linearGradient id="fog" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{SOUL}" stop-opacity="0"/>
  <stop offset="1" stop-color="{SOUL}" stop-opacity=".07"/></linearGradient>
<style>{css_common()}
.title{{filter:url(#glow)}}
</style></defs>"""
    body += f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    # distant pillars of a ruined city
    for i in range(14):
        x = 40 + i * 86 + rnd.uniform(-20, 20)
        h = rnd.uniform(120, 260)
        w = rnd.uniform(16, 34)
        body += (f'<rect x="{x:.0f}" y="{H - 90 - h:.0f}" width="{w:.0f}" height="{h:.0f}" fill="#0d1630" opacity=".8"/>'
                 f'<path d="M{x - 6:.0f},{H - 90 - h:.0f} h{w + 12:.0f} l-{(w + 12) / 2:.0f},-{rnd.uniform(14, 40):.0f} Z" fill="#0d1630" opacity=".8"/>')
        if rnd.random() < .45:
            body += (f'<rect x="{x + w / 2 - 2:.0f}" y="{H - 70 - h:.0f}" width="4" height="7" fill="{LANTERN}" '
                     f'opacity=".55" class="fl" style="animation-delay:-{rnd.uniform(0, 3):.1f}s"/>')
    body += f'<rect y="{H - 200}" width="{W}" height="200" fill="url(#fog)"/>'
    body += f'<path d="{jagged(W, 70, 26, 34, 11, True)}" fill="#0b1226"/>'
    body += f'<path d="{jagged(W, 38, 20, 26, 12, True)}" fill="{ABYSS}"/>'
    body += f'<path d="{jagged(W, H - 46, 18, 40, 13, False)}" fill="#0a1022"/>'
    body += f'<path d="{jagged(W, H - 22, 14, 30, 14, False)}" fill="{ABYSS}"/>'
    for i, (x, ln) in enumerate([(120, 70), (190, 120), (980, 95), (1060, 60), (1110, 140), (330, 50)]):
        body += vine(x, ln, 40 + i, bulb=i % 2 == 0 or ln > 100)
    body += spores(46, 0, W, 120, H, 5)
    # title block
    cx = W / 2
    body += t(cx, 150, "~  A TALE OF CODE AND CONSENSUS  ~", 15, MIST, SERIF, spacing=5)
    body += (f'<g class="title">{t(cx, 228, "SURYANSH SHARMA", 70, BONE, SERIF, spacing=10, weight="600")}</g>')
    body += flourish(cx, 262, 330)
    body += t(cx, 306, "Machine Learning  ·  Distributed Systems  ·  Multi-Agent Infrastructure", 21,
              "#c9d4e6", BODY, spacing=1.2)
    body += t(cx, 338, "NIT PATNA  —  COMPUTER SCIENCE  '27", 14, MIST, SERIF, spacing=4)
    body += f'<g class="bl">{t(cx, 404, "—  PRESS START  —", 15, LANTERN, SERIF, spacing=6)}</g>'
    body += wanderer(150, H - 62, 1.25)
    body += f'<rect width="{W}" height="{H}" filter="url(#grain)"/>'
    body += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{SLATE}"/>'
    write("hero.svg", svg(W, H, body, "Suryansh Sharma — a tale of code and consensus"))


def header(name, title):
    H = 70
    body = f"<defs>{defs_common()}<style>{css_common()}</style></defs>"
    body += flourish(W / 2, 36, 520, MIST, title)
    write(f"title-{name}.svg", svg(W, H, body, title))


def lore():
    H = 200
    body = f"<defs>{defs_common()}<style>{css_common()}</style></defs>"
    body += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{DEEP}" stroke="{SLATE}"/>'
    body += spores(14, 20, W - 20, 60, H, 21)
    lines = [
        "Beneath the surface lies a kingdom of half-built engines and long nights.",
        "Its wanderer trains models, teaches machines to agree, and sends small agents",
        "down into the dark to trade, remember and report back.",
    ]
    for i, s in enumerate(lines):
        body += t(W / 2, 62 + i * 34, s, 21, "#cfd8e8", BODY, extra=ITALIC)
    body += t(W / 2, 172, "— inscription found at the entrance", 13, MIST, SERIF, spacing=3)
    write("lore.svg", svg(W, H, body, "Lore: who Suryansh is"))


REGIONS = [
    # ornate name, repo, one-liner, centre, radii, tint
    ("THE CONSENSUS DEPTHS", "raftkv", "Raft from scratch in Go", (250, 190), (150, 92), SOUL),
    ("THE HIVE ARCHIVE", "hivemind", "graph memory for AI agents", (600, 140), (150, 80), LANTERN),
    ("THE TRADING HALLS", "agentic-trading-desk", "agents trading over MCP", (945, 205), (165, 95), MOSS),
    ("MERKEL REX EXCHANGE", "Cryptocurrency-Trading-Platform-", "C++ order-book engine", (790, 425), (140, 72), EMBER),
    ("HALL OF FOUR SENSES", "Multimodal-Sentiment-Analysis", "text · face · voice · video", (440, 405), (150, 78), VIOLET),
    ("THE TRAFFIC WASTES", "Traffic-Forecast", "geohash demand forecasting", (150, 430), (110, 64), MIST),
]
PATHS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (4, 5), (0, 5), (1, 4)]


def world_map():
    H = 540
    body = f"<defs>{defs_common()}<style>{css_common()}</style>"
    body += f"""<radialGradient id="parch" cx=".5" cy=".45" r=".7"><stop offset="0" stop-color="#121b33"/>
  <stop offset="1" stop-color="{ABYSS}"/></radialGradient></defs>"""
    body += f'<rect width="{W}" height="{H}" rx="14" fill="url(#parch)"/>'
    body += f'<rect width="{W}" height="{H}" rx="14" filter="url(#grain)"/>'
    # faint grid of a cartographer's sheet
    for x in range(60, W, 60):
        body += f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{SLATE}" stroke-width=".5" opacity=".5"/>'
    for y in range(60, H, 60):
        body += f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{SLATE}" stroke-width=".5" opacity=".5"/>'
    # tunnels between areas
    for a, b in PATHS:
        (x1, y1), (x2, y2) = REGIONS[a][3], REGIONS[b][3]
        mx, my = (x1 + x2) / 2 + (y2 - y1) * .12, (y1 + y2) / 2 - (x2 - x1) * .08
        body += (f'<path d="M{x1},{y1} Q{mx:.0f},{my:.0f} {x2},{y2}" fill="none" stroke="{INK}" '
                 f'stroke-width="9" stroke-linecap="round"/>'
                 f'<path d="M{x1},{y1} Q{mx:.0f},{my:.0f} {x2},{y2}" fill="none" stroke="{MIST}" '
                 f'stroke-width="1.2" stroke-dasharray="3 7" opacity=".7"/>')
    for i, (name, repo, line, (cx, cy), (rx, ry), tint) in enumerate(REGIONS):
        d = blob(cx, cy, rx, ry, 100 + i)
        body += f'<path d="{d}" fill="{STONE}"/>'
        body += (f'<path d="{d}" fill="{tint}" fill-opacity=".08" stroke="{tint}" stroke-opacity=".55" '
                 f'stroke-width="1.6" stroke-dasharray="7 4"/>')
        body += t(cx, cy - 6, name, 20, BONE, SERIF, spacing=3, weight="600")
        body += t(cx, cy + 20, repo if len(repo) < 26 else repo[:24] + "…", 16, tint, BODY)
        body += t(cx, cy + 42, line, 16, MIST, BODY, extra=ITALIC)
        body += (f'<circle cx="{cx}" cy="{cy - 44}" r="10" fill="{tint}" opacity=".25" class="pu" '
                 f'style="animation-delay:-{i * .45:.2f}s"/>'
                 f'<circle cx="{cx}" cy="{cy - 44}" r="3.5" fill="{tint}" filter="url(#glow)"/>')
    # "you are here" on the newest area
    hx, hy = REGIONS[1][3]
    body += (f'<g class="bl"><path d="M{hx + 118},{hy - 64} l10,-18 l10,18 Z" fill="{LANTERN}"/></g>'
             + t(hx + 128, hy - 90, "YOU ARE HERE", 11, LANTERN, SERIF, spacing=3))
    # compass rose
    ccx, ccy = 1090, 455
    body += (f'<g opacity=".8"><circle cx="{ccx}" cy="{ccy}" r="36" fill="none" stroke="{INK}" stroke-width="1.2"/>'
             f'<path d="M{ccx},{ccy - 46} L{ccx + 7},{ccy} L{ccx},{ccy + 46} L{ccx - 7},{ccy} Z" fill="{MIST}"/>'
             f'<path d="M{ccx - 46},{ccy} L{ccx},{ccy - 7} L{ccx + 46},{ccy} L{ccx},{ccy + 7} Z" fill="{INK}"/>'
             f'{t(ccx, ccy - 52, "N", 12, BONE, SERIF)}</g>')
    body += t(40, 40, "CARTOGRAPHER'S MAP  ·  KNOWN REGIONS", 13, MIST, SERIF, "start", spacing=4)
    body += spores(18, 0, W, 80, H, 31)
    body += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{SLATE}"/>'
    write("map.svg", svg(W, H, body, "Map of Suryansh's projects"))


PROJECTS = [
    dict(slug="raftkv", region="THE CONSENSUS DEPTHS", name="RaftKV", tint=SOUL, live=True,
         lines=["Fault-tolerant, strongly consistent key-value store on Raft, from scratch in Go",
                "with zero dependencies. Kill the leader: a new one is elected in ~150–300 ms",
                "without losing an acknowledged write. Partition it: no split-brain."],
         chips=["Go", "Pre-Vote", "check-quorum", "CRC32 WAL", "linearizable reads"],
         stat=("3×", "throughput from group commit")),
    dict(slug="hivemind", region="THE HIVE ARCHIVE", name="Hivemind", tint=LANTERN, live=True,
         lines=["Shared, time-aware graph memory for teams of AI coding agents (Claude Code,",
                "Cursor, Codex) on FalkorDB. Agents learn procedures by watching each other,",
                "see who is editing what, and never make the same mistake twice."],
         chips=["Python", "FalkorDB", "MCP", "Claude Code hooks", "Graph Hacks"],
         stat=("1×", "every mistake, made only once")),
    dict(slug="agentic-trading-desk", region="THE TRADING HALLS", name="Agentic Trading Desk",
         tint=MOSS, live=True,
         lines=["An orchestrator delegates to analyst, risk and execution agents that trade on",
                "a C++ order-book simulator exposed as an MCP server. Every order passes hard",
                "risk limits; an eval harness scores PnL, breaches and failed tool calls in CI."],
         chips=["Claude Agent SDK", "MCP", "C++", "Docker", "eval harness"],
         stat=("3,540", "real orders replayed")),
]


def project_card(p):
    H = 250
    tint = p["tint"]
    body = f"<defs>{defs_common()}<style>{css_common()}</style>"
    body += f"""<linearGradient id="cardbg" x1="0" x2="1"><stop offset="0" stop-color="{STONE}"/>
  <stop offset="1" stop-color="{DEEP}"/></linearGradient></defs>"""
    body += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#cardbg)" stroke="{SLATE}"/>'
    body += f'<rect x="0" y="0" width="5" height="{H}" rx="2" fill="{tint}" opacity=".8"/>'
    body += f'<circle cx="{W - 140}" cy="{H / 2}" r="150" fill="{tint}" opacity=".05"/>'
    body += t(44, 46, f"AREA DISCOVERED  ·  {p['region']}", 13, tint, SERIF, "start", spacing=4)
    body += t(44, 92, p["name"], 38, BONE, SERIF, "start", spacing=2, weight="600")
    for i, s in enumerate(p["lines"]):
        body += t(44, 128 + i * 25, s, 17, "#c3cee0", BODY, "start")
    x = 44
    for c in p["chips"]:
        w = len(c) * 8.2 + 26
        body += (f'<rect x="{x}" y="{H - 44}" width="{w:.0f}" height="26" rx="13" fill="none" '
                 f'stroke="{INK}"/>' + t(x + w / 2, H - 26, c, 14, MIST, BODY))
        x += w + 10
    # right column: the stat and a lit lantern pin
    sx = W - 150
    body += (f'<circle cx="{sx}" cy="88" r="42" fill="none" stroke="{tint}" stroke-opacity=".4"/>'
             f'<circle cx="{sx}" cy="88" r="52" fill="none" stroke="{tint}" stroke-opacity=".15" '
             f'stroke-dasharray="2 6"/>'
             + t(sx, 98, p["stat"][0], 28 if len(p["stat"][0]) < 4 else 22, tint, SERIF, weight="600",
                 extra='filter="url(#glow)"')
             + t(sx, 166, p["stat"][1], 15, MIST, BODY, extra=ITALIC))
    if p["live"]:
        body += (f'<circle cx="{sx - 34}" cy="{H - 31}" r="4" fill="{MOSS}" class="bl"/>'
                 + t(sx - 22, H - 26, "LIVE DEMO  ·  ENTER  →", 12, BONE, SERIF, "start", spacing=2))
    body += spores(8, W - 320, W - 20, 40, H, len(p["slug"]) * 17, (tint, BONE))
    write(f"project-{p['slug']}.svg", svg(W, H, body, f"{p['name']} project card"))


RELICS = [
    ("1826", "LEETCODE", "max rating · 650+ solved", SOUL, "gem"),
    ("3★", "CODECHEF", "max rating 1621", LANTERN, "star"),
    ("MLSS", "AMAZON", "ML Summer School '26", EMBER, "flame"),
    ("FINAL", "META × PYTORCH", "OpenEnv grand finale", VIOLET, "crown"),
    ("8.17", "NIT PATNA", "CGPA · CSE '27", MOSS, "key"),
]


def relic_icon(kind, cx, cy, c):
    if kind == "gem":
        return (f'<path d="M{cx},{cy - 22} L{cx + 18},{cy - 6} L{cx},{cy + 22} L{cx - 18},{cy - 6} Z" '
                f'fill="{c}" fill-opacity=".15" stroke="{c}" stroke-width="1.6"/>'
                f'<path d="M{cx - 18},{cy - 6} H{cx + 18} M{cx},{cy - 22} L{cx - 6},{cy - 6} L{cx},{cy + 22} '
                f'L{cx + 6},{cy - 6} Z" fill="none" stroke="{c}" stroke-width="1" opacity=".7"/>')
    if kind == "star":
        pts = " ".join(f"{cx + math.cos(math.pi / 2 + i * math.pi / 5) * (20 if i % 2 == 0 else 8):.1f},"
                       f"{cy - math.sin(math.pi / 2 + i * math.pi / 5) * (20 if i % 2 == 0 else 8):.1f}"
                       for i in range(10))
        return f'<polygon points="{pts}" fill="{c}" fill-opacity=".15" stroke="{c}" stroke-width="1.6"/>'
    if kind == "flame":
        return (f'<path d="M{cx},{cy - 24} C{cx + 18},{cy - 6} {cx + 16},{cy + 20} {cx},{cy + 20} '
                f'C{cx - 16},{cy + 20} {cx - 18},{cy - 4} {cx - 4},{cy - 10} C{cx - 4},{cy - 2} {cx + 2},{cy} '
                f'{cx},{cy - 24} Z" fill="{c}" fill-opacity=".15" stroke="{c}" stroke-width="1.6" class="fl"/>')
    if kind == "crown":
        return (f'<path d="M{cx - 20},{cy + 14} L{cx - 22},{cy - 12} L{cx - 9},{cy} L{cx},{cy - 20} '
                f'L{cx + 9},{cy} L{cx + 22},{cy - 12} L{cx + 20},{cy + 14} Z" fill="{c}" fill-opacity=".15" '
                f'stroke="{c}" stroke-width="1.6"/>')
    return (f'<circle cx="{cx - 8}" cy="{cy - 8}" r="10" fill="{c}" fill-opacity=".15" stroke="{c}" '
            f'stroke-width="1.6"/><path d="M{cx - 1},{cy - 1} L{cx + 18},{cy + 18} M{cx + 10},{cy + 10} '
            f'l6,-6 M{cx + 15},{cy + 15} l5,-5" stroke="{c}" stroke-width="1.8" fill="none"/>')


def relics():
    H = 270
    body = f"<defs>{defs_common()}<style>{css_common()}</style></defs>"
    body += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{DEEP}" stroke="{SLATE}"/>'
    step = (W - 80) / len(RELICS)
    for i, (big, name, sub, c, kind) in enumerate(RELICS):
        cx = 40 + step * (i + .5)
        body += (f'<circle cx="{cx}" cy="86" r="50" fill="url(#soullight)" opacity=".35" class="pu" '
                 f'style="animation-delay:-{i * .6:.1f}s"/>'
                 f'<circle cx="{cx}" cy="86" r="44" fill="{STONE}" stroke="{INK}" stroke-width="1.4"/>'
                 f'<circle cx="{cx}" cy="86" r="38" fill="none" stroke="{c}" stroke-opacity=".3" '
                 f'stroke-dasharray="1 5"/>')
        body += f'<g filter="url(#glow)">{relic_icon(kind, cx, 86, c)}</g>'
        body += t(cx, 172, big, 30, BONE, SERIF, weight="600", spacing=1)
        body += t(cx, 202, name, 15, c, SERIF, spacing=3)
        body += t(cx, 230, sub, 17, MIST, BODY, extra=ITALIC)
    body += spores(12, 0, W, 100, H, 51)
    write("relics.svg", svg(W, H, body, "Relics: competitive programming and achievements"))


JOURNAL = [
    ("Machine Learning Engineer Intern", "Trialshopy", "QUEST COMPLETE", MOSS),
    ("Data Scientist Intern", "Prodigy Infotech", "QUEST COMPLETE", MOSS),
    ("Your team here?", "an open slot in the party", "SEND A RAVEN  ↓", LANTERN),
]


def journal():
    H = 250
    body = f"<defs>{defs_common()}<style>{css_common()}</style></defs>"
    body += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{DEEP}" stroke="{SLATE}"/>'
    body += f'<line x1="70" y1="40" x2="70" y2="{H - 40}" stroke="{INK}" stroke-width="1.4" stroke-dasharray="2 6"/>'
    for i, (role, org, status, c) in enumerate(JOURNAL):
        y = 62 + i * 64
        open_ = i == len(JOURNAL) - 1
        body += (f'<path d="M70,{y - 10} L80,{y} L70,{y + 10} L60,{y} Z" fill="{DEEP if open_ else c}" '
                 f'stroke="{c}" stroke-width="1.4"' + (' class="bl"/>' if open_ else "/>"))
        body += t(104, y + 7, role, 22, BONE if not open_ else MIST, SERIF, "start", spacing=1, weight="600")
        body += t(104 + len(role) * 14.2 + 22, y + 6, "— " + org, 17, MIST, BODY, "start",
                  extra=ITALIC)
        body += t(W - 60, y + 6, status, 13, c, SERIF, "end", spacing=3)
        if not open_:
            body += f'<line x1="104" y1="{y + 30}" x2="{W - 60}" y2="{y + 30}" stroke="{SLATE}"/>'
    write("journal.svg", svg(W, H, body, "Journal: experience"))


INVENTORY = ["C++", "Python", "Go", "JavaScript", "SQL", "PyTorch", "Hugging Face", "Django",
             "MERN", "FalkorDB", "MCP", "Docker"]
LANG_COLORS = {"Python": SOUL, "JavaScript": LANTERN, "Go": MOSS, "C++": EMBER, "Dockerfile": VIOLET,
               "Shell": MIST, "TypeScript": SOUL}


def inventory(langs, n_repos):
    H = 400
    body = f"<defs>{defs_common()}<style>{css_common()}</style></defs>"
    body += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="{DEEP}" stroke="{SLATE}"/>'
    # left: equipment slots
    body += t(40, 48, "EQUIPPED", 13, MIST, SERIF, "start", spacing=4)
    cols, sw, sh, gap = 4, 128, 58, 12
    for i, name in enumerate(INVENTORY):
        x, y = 40 + (i % cols) * (sw + gap), 68 + (i // cols) * (sh + gap)
        body += (f'<rect x="{x}" y="{y}" width="{sw}" height="{sh}" rx="8" fill="{STONE}" stroke="{INK}"/>'
                 f'<path d="M{x + 6},{y + 6} h10 M{x + 6},{y + 6} v10 M{x + sw - 6},{y + sh - 6} h-10 '
                 f'M{x + sw - 6},{y + sh - 6} v-10" stroke="{MIST}" stroke-width="1" opacity=".5"/>'
                 + t(x + sw / 2, y + sh / 2 + 6, name, 17 if len(name) < 11 else 15, BONE, BODY))
    body += t(40, 300, "Also wielded: computer vision, NLP, affective computing", 15, MIST, BODY, "start", extra=ITALIC)
    body += t(40, 322, "(EEG and eye-tracking), gradient boosting, Raft, Flask.", 15, MIST, BODY, "start", extra=ITALIC)
    # right: soul essence (real language bytes)
    ex = 660
    body += t(ex, 48, "SOUL ESSENCE  ·  CODE BY LANGUAGE", 13, MIST, SERIF, "start", spacing=4)
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    total = sum(v for _, v in top) or 1
    for i, (name, v) in enumerate(top):
        y = 84 + i * 42
        pct = 100 * v / total
        c = LANG_COLORS.get(name, MIST)
        bw = 300 * v / top[0][1]
        body += t(ex, y + 5, name, 16, BONE, BODY, "start")
        body += (f'<rect x="{ex + 120}" y="{y - 8}" width="300" height="14" rx="7" fill="{STONE}" stroke="{INK}"/>'
                 f'<rect x="{ex + 120}" y="{y - 8}" width="{max(bw, 8):.0f}" height="14" rx="7" fill="{c}" '
                 f'fill-opacity=".8" filter="url(#glow)"/>'
                 + t(W - 40, y + 5, f"{pct:.1f}%", 14, MIST, BODY, "end"))
    body += t(ex, 350, f"Measured across {n_repos} public repositories; notebooks and markup left out.",
              15, MIST, BODY, "start", extra=ITALIC)
    body += t(ex, 372, "Refreshed daily by a workflow in this repo.", 13, MIST, BODY, "start",
              extra=ITALIC)
    write("inventory.svg", svg(W, H, body, "Inventory: stack and language breakdown"))


def footer():
    H = 260
    body = f"<defs>{defs_common()}<style>{css_common()}</style></defs>"
    body += f'<rect width="{W}" height="{H}" rx="14" fill="{ABYSS}"/>'
    body += f'<path d="{jagged(W, H - 30, 12, 34, 61, False)}" fill="#0a1022"/>'
    # resting stone with the wanderer seated beside the lantern
    body += f'<path d="M520,{H - 34} q80,-26 160,0 Z" fill="{STONE}" stroke="{INK}"/>'
    body += wanderer(600, H - 64, 1.1)
    body += spores(24, 400, 800, 80, H, 71, (LANTERN, LANTERN, SOUL))
    body += t(W / 2, 60, "YOU REST BY THE LANTERN.  PROGRESS SAVED.", 18, BONE, SERIF, spacing=5)
    body += f'<g class="bl">{t(W / 2, 92, "thank you for exploring", 15, MIST, BODY, extra=ITALIC)}</g>'
    body += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{SLATE}"/>'
    write("footer.svg", svg(W, H, body, "Footer: progress saved"))


def main():
    ASSETS.mkdir(exist_ok=True)
    langs, n_repos = fetch_stats("--offline" in sys.argv)
    hero()
    lore()
    for name, title in [("map", "THE MAP"), ("areas", "AREAS DISCOVERED"), ("relics", "RELICS"),
                        ("journal", "JOURNAL"), ("inventory", "INVENTORY"), ("raven", "SEND A RAVEN")]:
        header(name, title)
    world_map()
    for p in PROJECTS:
        project_card(p)
    relics()
    journal()
    inventory(langs, n_repos)
    footer()


if __name__ == "__main__":
    main()

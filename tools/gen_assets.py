"""Generate every SVG on the Lecrupus profile README.

    python tools/gen_assets.py            # uses GITHUB_TOKEN if set, else unauthenticated API
    python tools/gen_assets.py --offline  # skip the API, use the fallback numbers below

The README is one descent through a cave. GitHub's dark background is the rock; every panel is
a hollow carved into it, so the panels join into one continuous cross-section. Each project
chamber animates the project's real mechanism: Raft leader election, agents writing to a shared
memory graph, an order passing a risk gate into an order book.

All art is raw SVG: no raster images, no external fonts, no third-party widgets. The "carried"
panel's language bar is the only live data; .github/workflows/refresh.yml reruns this daily.
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
ASSETS = Path(__file__).resolve().parent.parent / "assets"
W = 1200

# ── palette: one ground (the rock), one ink, one accent (lantern light) ─────────────────────────
ROCK = "#0d1117"       # GitHub's dark background, so panel edges vanish into the page
INK = "#ece6da"        # bone
DIM = "#9aa3ad"        # secondary notes only
LANTERN = "#f2bd5c"    # the accent: leaders, the hero claim, the resting lantern
SOUL = "#8fd8e8"       # follower lights, spores
MOSS = "#7cc79a"       # bids, approvals
EMBER = "#ef7d55"      # asks, rejections

# One flat field per depth: the deeper the chamber, the warmer and darker the stone.
FIELD = {"surface": "#101b2c", "raft": "#0f1d22", "hive": "#1b150d", "desk": "#0f1a14",
         "relics": "#15161c", "carry": "#111a22", "rest": "#0f1726"}
STEP = {"surface": "#16243a", "raft": "#15282f", "hive": "#271e12", "desk": "#16251c",
        "relics": "#1d1e26", "carry": "#18232d", "rest": "#16203a"}

FACE = "'Palatino Linotype','Book Antiqua',Palatino,'URW Palladio L','TeX Gyre Pagella',Georgia,serif"

FALLBACK_LANGS = {"Python": 432350, "JavaScript": 244953, "Go": 92392, "C++": 58222,
                  "Dockerfile": 9011, "Shell": 5978}
FALLBACK_REPOS = 25
SKIP_LANGS = {"Jupyter Notebook", "HTML", "CSS", "Batchfile", "PowerShell", "Makefile"}


# ── helpers ──────────────────────────────────────────────────────────────────────────────────────
def svg(height, body, title, css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
            f'viewBox="0 0 {W} {height}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title><defs>{DEFS}<style>{CSS}{css}</style></defs>'
            f'<rect width="{W}" height="{height}" fill="{ROCK}"/>{body}</svg>\n')


def write(name, content):
    (ASSETS / name).write_text(content, encoding="utf-8")
    print(f"  wrote assets/{name}  ({len(content) // 1024} KB)")


def text(x, y, s, size, fill=INK, anchor="start", weight="400", italic=False, extra=""):
    style = ' font-style="italic"' if italic else ""
    track = ' letter-spacing="-1"' if size >= 60 else ""
    return (f'<text x="{x}" y="{y}" font-family="{FACE}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{style}{track} {extra}>{escape(s)}</text>')


def lines(x, y, rows, size, fill=INK, lead=1.5, **kw):
    return "".join(text(x, y + i * size * lead, r, size, fill, **kw) for i, r in enumerate(rows))


# Light is the one thing allowed to glow: it is what a cave has instead of decoration.
DEFS = f"""
<filter id="light" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.4" result="b"/>
<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<radialGradient id="pool"><stop offset="0" stop-color="{LANTERN}" stop-opacity=".42"/><stop offset="1" stop-color="{LANTERN}" stop-opacity="0"/></radialGradient>
<radialGradient id="coldpool"><stop offset="0" stop-color="{SOUL}" stop-opacity=".35"/><stop offset="1" stop-color="{SOUL}" stop-opacity="0"/></radialGradient>
"""

CSS = """
@keyframes rise1{0%{transform:translate(0,0);opacity:0}15%{opacity:.85}100%{transform:translate(14px,-240px);opacity:0}}
@keyframes rise2{0%{transform:translate(0,0);opacity:0}20%{opacity:.6}100%{transform:translate(-18px,-280px);opacity:0}}
@keyframes flicker{0%,100%{opacity:.9}14%{opacity:.62}22%{opacity:.96}50%{opacity:.72}63%{opacity:1}81%{opacity:.78}}
@keyframes sway{0%,100%{transform:rotate(-3deg)}50%{transform:rotate(3deg)}}
@keyframes blinkeyes{0%,93%,100%{transform:scaleY(1)}96%{transform:scaleY(.1)}}
@keyframes breathe{0%,100%{opacity:.45}50%{opacity:1}}
.fl{animation:flicker 3.4s infinite}
.sw{transform-box:fill-box;transform-origin:50% 0;animation:sway 7s ease-in-out infinite}
.ey{transform-box:fill-box;transform-origin:center;animation:blinkeyes 6s infinite}
.br{animation:breathe 3s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def hollow(x0, y0, x1, y1, seed, fill, roof=26, floor=16):
    """A cave pocket: stalactite roof, uneven walls, rubble floor. Returns a closed path."""
    rnd = random.Random(seed)
    pts = []
    x = x0
    while x < x1:  # roof, left to right
        if rnd.random() < .18:
            pts += [(x, y0 + rnd.uniform(0, 8)), (x + 9, y0 + rnd.uniform(roof * 1.4, roof * 2.6)),
                    (x + 18, y0 + rnd.uniform(0, 8))]
            x += 18
        else:
            pts.append((x, y0 + rnd.uniform(0, roof * .55)))
        x += rnd.uniform(22, 46)
    y = y0
    while y < y1:  # right wall, downwards
        pts.append((x1 - rnd.uniform(0, 14), y))
        y += rnd.uniform(40, 80)
    x = x1
    while x > x0:  # floor, right to left
        pts.append((x, y1 - rnd.uniform(0, floor)))
        x -= rnd.uniform(26, 60)
    y = y1
    while y > y0:  # left wall, upwards
        pts.append((x0 + rnd.uniform(0, 14), y))
        y -= rnd.uniform(40, 80)
    return f'<path d="M{" L".join(f"{px:.0f},{py:.0f}" for px, py in pts)} Z" fill="{fill}"/>'


def spores(n, x0, x1, y0, y1, seed, colors=(SOUL, SOUL, INK, LANTERN)):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        dur = rnd.uniform(8, 17)
        out.append(f'<circle cx="{rnd.uniform(x0, x1):.0f}" cy="{rnd.uniform(y0, y1):.0f}" '
                   f'r="{rnd.choice((1, 1.3, 1.6, 2.1))}" fill="{rnd.choice(colors)}" filter="url(#light)" '
                   f'style="animation:rise{rnd.randint(1, 2)} {dur:.1f}s linear {-rnd.uniform(0, dur):.1f}s infinite"/>')
    return "".join(out)


def wanderer(x, y, s=1.0, seated=False):
    """An original hooded lantern-bearer."""
    legs = ('<path d="M-22,26 C-10,30 14,30 30,22 L30,31 L-24,31 Z" fill="#090d18"/>' if seated else "")
    return f"""
<g transform="translate({x},{y}) scale({s})">
  <circle cx="30" cy="-46" r="80" fill="url(#pool)" class="fl"/>
  {legs}
  <path d="M0,-40 C-15,-37 -21,-8 -23,20 L-28,31 L-8,27 L0,32 L9,27 L28,31 L23,20 C21,-8 15,-37 0,-40 Z" fill="#090d18"/>
  <path d="M-14,-27 C-15,-52 15,-52 14,-27 C13,-15 -13,-15 -14,-27 Z" fill="#0c1222"/>
  <ellipse cx="0" cy="-26" rx="8.5" ry="7.5" fill="#010207"/>
  <g class="ey"><ellipse cx="-3.6" cy="-27" rx="1.7" ry="2.3" fill="{SOUL}" filter="url(#light)"/>
  <ellipse cx="3.6" cy="-27" rx="1.7" ry="2.3" fill="{SOUL}" filter="url(#light)"/></g>
  <line x1="17" y1="31" x2="23" y2="-56" stroke="#3d3022" stroke-width="2.8" stroke-linecap="round"/>
  <path d="M23,-56 q8,-2 9,6" fill="none" stroke="#3d3022" stroke-width="2.2"/>
  <g class="sw" style="transform-origin:32px -50px">
    <line x1="32" y1="-50" x2="32" y2="-44" stroke="{DIM}" stroke-width="1"/>
    <path d="M27,-44 h10 l-1.5,12 h-7 Z" fill="{LANTERN}" class="fl" filter="url(#light)"/>
    <path d="M26,-44 h12 M27,-32 h10" stroke="#5b4630" stroke-width="1.8"/>
  </g>
</g>"""


def vine(x, top, length, seed, bulb=True):
    rnd = random.Random(seed)
    d, y = f"M{x},{top}", top
    while y < top + length:
        y2 = min(top + length, y + rnd.uniform(18, 30))
        d += f" Q{x + rnd.uniform(-8, 8):.0f},{(y + y2) / 2:.0f} {x + rnd.uniform(-3, 3):.0f},{y2:.0f}"
        y = y2
    out = (f'<g class="sw" style="animation-duration:{rnd.uniform(5, 9):.1f}s;animation-delay:-{rnd.uniform(0, 5):.1f}s">'
           f'<path d="{d}" fill="none" stroke="#1c2a3e" stroke-width="2.2"/>')
    if bulb:
        out += (f'<circle cx="{x}" cy="{top + length + 6}" r="18" fill="url(#coldpool)" class="fl"/>'
                f'<circle cx="{x}" cy="{top + length + 6}" r="4" fill="{SOUL}" filter="url(#light)"/>')
    return out + "</g>"


# ── live data ────────────────────────────────────────────────────────────────────────────────────
def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "lecrupus-profile"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
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


# ── the surface: who, and the claim the chambers prove ───────────────────────────────────────────
def hero():
    H = 600
    rnd = random.Random(3)
    b = hollow(0, 0, W, H - 20, 1, FIELD["surface"], roof=30, floor=10)
    # far city: flat silhouettes, two tone steps, lit windows
    for layer, (tone, base, hmin, hmax) in enumerate([(STEP["surface"], H - 150, 140, 300),
                                                      ("#13203a", H - 120, 80, 200)]):
        x = 560 + layer * 30
        while x < W:
            w, h = rnd.uniform(18, 40), rnd.uniform(hmin, hmax)
            b += (f'<rect x="{x:.0f}" y="{base - h:.0f}" width="{w:.0f}" height="{h + 160:.0f}" fill="{tone}"/>'
                  f'<path d="M{x - 5:.0f},{base - h:.0f} h{w + 10:.0f} l-{(w + 10) / 2:.0f},-{rnd.uniform(16, 46):.0f} Z" fill="{tone}"/>')
            for _ in range(rnd.randint(0, 2)):
                b += (f'<rect x="{x + rnd.uniform(4, w - 8):.0f}" y="{base - h + rnd.uniform(20, h * .7):.0f}" width="4" height="7" '
                      f'fill="{LANTERN}" opacity=".7" class="fl" style="animation-delay:-{rnd.uniform(0, 3):.1f}s"/>')
            x += w + rnd.uniform(14, 46)
    # the ledge the wanderer stands on, and the shaft that drops into the next panel
    b += f'<path d="M380,{H} C480,{H - 30} 560,{H - 100} 700,{H - 112} C820,{H - 120} 900,{H - 104} 1000,{H - 112} L1000,{H} Z" fill="{ROCK}"/>'
    b += f'<path d="M990,{H} L990,{H - 112} C1060,{H - 118} 1130,{H - 96} 1200,{H - 104} L1200,{H} Z" fill="{ROCK}"/>'
    for i, (x, top, ln) in enumerate([(610, 20, 70), (680, 24, 130), (1090, 18, 90), (1150, 22, 150), (860, 16, 50)]):
        b += vine(x, top, ln, 40 + i, bulb=ln > 60)
    b += spores(36, 520, W, 140, H - 60, 5)
    b += wanderer(900, H - 146, 1.5)
    # left column: the name, set very large; one claim; one line of who
    b += text(64, 236, "Suryansh", 132, INK, weight="600")
    b += text(64, 372, "Sharma", 132, INK, weight="600")
    b += text(68, 448, "The deeper the system,", 30, LANTERN)
    b += text(68, 490, "the brighter the lantern.", 30, LANTERN)
    b += text(68, 548, "NIT Patna, CSE '27", 22, DIM)
    write("hero.svg", svg(H, b, "Suryansh Sharma. The deeper the system, the brighter the lantern."))


# ── chamber one: RaftKV, five nodes electing a leader ───────────────────────────────────────────
RAFT_CSS = """
@keyframes leadA{0%,46%{opacity:1}50%,100%{opacity:0}}
@keyframes downA{0%,46%{opacity:0}50%,100%{opacity:1}}
@keyframes candC{0%,49%{opacity:0}51%,55%{opacity:1}52%,54%{opacity:.2}57%,100%{opacity:0}}
@keyframes leadC{0%,55%{opacity:0}58%,100%{opacity:1}}
@keyframes hbA{0%,2%{opacity:0}4%,44%{opacity:1}46%,100%{opacity:0}}
@keyframes vote{0%,50%{opacity:0}51%,56%{opacity:1}58%,100%{opacity:0}}
@keyframes hbC{0%,58%{opacity:0}60%,98%{opacity:1}100%{opacity:0}}
@keyframes cap1{0%,46%{opacity:1}49%,100%{opacity:0}}
@keyframes cap2{0%,47%{opacity:0}50%,56%{opacity:1}58%,100%{opacity:0}}
@keyframes cap3{0%,57%{opacity:0}60%,98%{opacity:1}100%{opacity:0}}
.T{animation-duration:16s;animation-iteration-count:infinite;animation-timing-function:linear}
"""


def pulses(src, dsts, color, dur, cls):
    out = f'<g class="T" style="animation-name:{cls}">'
    for i, d in enumerate(dsts):
        out += (f'<circle r="4" fill="{color}" filter="url(#light)"><animateMotion dur="{dur}s" '
                f'begin="{i * .12:.2f}s" repeatCount="indefinite" path="M{src[0]},{src[1]} L{d[0]},{d[1]}"/></circle>')
    return out + "</g>"


def chamber_raft():
    H = 500
    b = hollow(20, 10, W - 20, H - 10, 21, FIELD["raft"])
    b += spores(14, 40, W - 40, 120, H - 20, 22)
    # text on the left
    b += text(70, 132, "RaftKV", 60, INK, weight="600")
    b += text(72, 182, "Machines that agree.", 30, SOUL)
    b += lines(72, 240, ["A fault-tolerant key-value store on Raft,",
                         "written from scratch in Go.",
                         "Kill the leader: a new one is elected in",
                         "130–180 ms and no acknowledged write",
                         "is lost. Partition it: nothing splits."], 23, INK)
    b += text(72, 446, "Group commit: 3× throughput, 4.5× lower p99", 20, DIM)
    # five nodes on stone pillars
    nodes = [(650, 320), (770, 220), (905, 180), (1040, 220), (1120, 330)]
    A, C = nodes[0], nodes[2]
    floor = H - 26
    for i, (x, y) in enumerate(nodes):
        b += f'<path d="M{x - 16},{floor} L{x - 11},{y + 18} L{x + 11},{y + 18} L{x + 16},{floor} Z" fill="{STEP["raft"]}"/>'
        b += f'<rect x="{x - 20}" y="{y + 12}" width="40" height="9" fill="{STEP["raft"]}"/>'
        b += text(x, floor - 14, f"node {i + 1}", 19, DIM, "middle")
    # links (the cluster's network), faint
    for i, p in enumerate(nodes):
        for q in nodes[i + 1:]:
            b += f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="{SOUL}" stroke-opacity=".12" stroke-width="1.5"/>'
    b += pulses(A, [n for n in nodes if n != A], LANTERN, 1.3, "hbA")
    b += pulses(C, [n for n in nodes if n not in (A, C)], SOUL, .8, "vote")
    b += pulses(C, [n for n in nodes if n not in (A, C)], LANTERN, 1.3, "hbC")
    for x, y in nodes:  # follower lights
        if (x, y) not in (A, C):
            b += (f'<circle cx="{x}" cy="{y}" r="22" fill="url(#coldpool)" class="br"/>'
                  f'<circle cx="{x}" cy="{y}" r="7" fill="{SOUL}" filter="url(#light)"/>')
    # node 1: leader, then down
    b += (f'<g class="T" style="animation-name:leadA"><circle cx="{A[0]}" cy="{A[1]}" r="46" fill="url(#pool)" class="fl"/>'
          f'<circle cx="{A[0]}" cy="{A[1]}" r="11" fill="{LANTERN}" filter="url(#light)"/></g>'
          f'<g class="T" style="animation-name:downA"><circle cx="{A[0]}" cy="{A[1]}" r="8" fill="#3a3f47"/>'
          f'<path d="M{A[0] - 6},{A[1] - 6} l12,12 M{A[0] + 6},{A[1] - 6} l-12,12" stroke="{EMBER}" stroke-width="2"/></g>')
    # node 3: follower, candidate, leader
    b += (f'<g class="T" style="animation-name:cap1"><circle cx="{C[0]}" cy="{C[1]}" r="7" fill="{SOUL}" filter="url(#light)"/></g>'
          f'<g class="T" style="animation-name:candC"><circle cx="{C[0]}" cy="{C[1]}" r="9" fill="{INK}" filter="url(#light)"/></g>'
          f'<g class="T" style="animation-name:leadC"><circle cx="{C[0]}" cy="{C[1]}" r="46" fill="url(#pool)" class="fl"/>'
          f'<circle cx="{C[0]}" cy="{C[1]}" r="11" fill="{LANTERN}" filter="url(#light)"/></g>')
    # the running caption
    cx, cy = 885, 96
    b += (f'<g class="T" style="animation-name:cap1">{text(cx, cy, "Node 1 leads term 7 and sends heartbeats", 22, INK, "middle")}</g>'
          f'<g class="T" style="animation-name:cap2">{text(cx, cy, "Node 1 is down. Node 3 asks for votes", 22, EMBER, "middle")}</g>'
          f'<g class="T" style="animation-name:cap3">{text(cx, cy, "Node 3 wins term 8. No write was lost", 22, LANTERN, "middle")}</g>')
    write("chamber-raftkv.svg", svg(H, b, "RaftKV: five nodes elect a new leader when the old one fails", RAFT_CSS))


# ── chamber two: Hivemind, agents writing to a shared memory graph ──────────────────────────────
def hexagon(cx, cy, r):
    return " ".join(f"{cx + r * math.cos(math.pi / 3 * k + math.pi / 6):.1f},"
                    f"{cy + r * math.sin(math.pi / 3 * k + math.pi / 6):.1f}" for k in range(6))


def chamber_hive():
    H = 500
    rnd = random.Random(31)
    b = hollow(20, 10, W - 20, H - 10, 32, FIELD["hive"])
    b += spores(12, 40, W - 40, 120, H - 20, 33, (LANTERN, LANTERN, INK))
    # honeycomb on the left
    ox, oy, r = 330, 245, 34
    cells = []
    for q in range(-3, 4):
        for s in range(-2, 3):
            x = ox + r * math.sqrt(3) * (q + (s % 2) * .5)
            y = oy + r * 1.5 * s
            if math.hypot(x - ox, (y - oy) * 1.25) < 190:
                cells.append((x, y))
    def near(i, j):
        return 0 < math.dist(cells[i], cells[j]) < r * 2.1

    lit = [len(cells) // 2]
    while len(lit) < 9:  # a random walk through adjacent cells, so each edge is short
        options = [j for j in range(len(cells)) if near(lit[-1], j) and j not in lit]
        if not options:
            break
        lit.append(rnd.choice(options))
    for i, (x, y) in enumerate(cells):
        b += f'<polygon points="{hexagon(x, y, r - 3)}" fill="{STEP["hive"]}"/>'
    for n, i in enumerate(lit):  # memories being written: each cell warms, holds, cools
        x, y = cells[i]
        b += (f'<polygon points="{hexagon(x, y, r - 3)}" fill="{LANTERN}" opacity="0">'
              f'<animate attributeName="opacity" values="0;0;.75;.75;0" keyTimes="0;.08;.18;.75;1" dur="12s" '
              f'begin="{-n * 1.3:.1f}s" repeatCount="indefinite"/></polygon>')
    # graph edges between remembered cells, drawn and erased
    for n in range(len(lit) - 1):
        (x1, y1), (x2, y2) = cells[lit[n]], cells[lit[n + 1]]
        ln = math.hypot(x2 - x1, y2 - y1)
        b += (f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{INK}" stroke-width="3" '
              f'stroke-linecap="round" stroke-dasharray="{ln:.0f}" stroke-dashoffset="{ln:.0f}" opacity=".8">'
              f'<animate attributeName="stroke-dashoffset" values="{ln:.0f};{ln:.0f};0;0;{ln:.0f}" keyTimes="0;.2;.35;.8;1" '
              f'dur="12s" begin="{-n * 1.7:.1f}s" repeatCount="indefinite"/></line>')
    # three agents flying between cells
    for k, dur in enumerate((9, 11, 13)):
        route = rnd.sample(cells, 5)
        d = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in route) + " Z"
        b += (f'<g><circle r="5" fill="{SOUL}" filter="url(#light)"/><circle r="14" fill="url(#coldpool)"/>'
              f'<animateMotion dur="{dur}s" repeatCount="indefinite" path="{d}"/></g>')
    b += text(330, 468, "Claude Code, Cursor and Codex, one memory", 19, DIM, "middle")
    # text on the right
    tx = 640
    b += text(tx, 132, "Hivemind", 60, INK, weight="600")
    b += text(tx + 2, 182, "Agents that remember.", 30, LANTERN)
    b += lines(tx + 2, 240, ["Shared, time-aware graph memory for",
                             "teams of AI coding agents, in FalkorDB.",
                             "Agents learn procedures by watching",
                             "each other, see who is editing what,",
                             "and make each mistake only once."], 23, INK)
    b += text(tx + 2, 446, "Python · FalkorDB · MCP · Graph Hacks", 20, DIM)
    write("chamber-hivemind.svg", svg(H, b, "Hivemind: agents writing memories into a shared graph"))


# ── chamber three: the trading desk, an order meets the risk gate ────────────────────────────────
def chamber_desk():
    H = 600
    b = hollow(20, 10, W - 20, H - 10, 41, FIELD["desk"])
    b += spores(12, 40, W - 40, 160, H - 20, 42, (MOSS, INK, SOUL))
    b += text(70, 132, "Agentic Trading Desk", 60, INK, weight="600")
    b += text(72, 182, "Agents that trade.", 30, MOSS)
    b += lines(72, 238, ["An orchestrator hands work to analyst, risk and execution agents that",
                         "trade on a C++ order book served over MCP. Every order meets hard limits."], 23, INK)
    # the floor of the chamber: agents on posts, then the order book
    base = H - 60
    agents = [("analyst", 150), ("risk", 360), ("execution", 570)]
    for name, x in agents:
        b += (f'<path d="M{x - 18},{base} L{x - 10},{base - 120} L{x + 10},{base - 120} L{x + 18},{base} Z" fill="{STEP["desk"]}"/>'
              f'<circle cx="{x}" cy="{base - 140}" r="34" fill="url(#coldpool)" class="br"/>'
              f'<circle cx="{x}" cy="{base - 140}" r="8" fill="{SOUL}" filter="url(#light)"/>'
              + text(x, base + 32, name, 20, DIM, "middle"))
    # order book: bids (left of the spread) and asks (right), price levels as slabs
    mx, top = 900, base - 190
    levels = [(110, 70), (150, 120), (190, 95), (130, 160), (80, 115)]
    for i, (bid, ask) in enumerate(levels):
        y = top + i * 34
        b += f'<rect x="{mx - 14 - bid}" y="{y}" width="{bid}" height="24" fill="{MOSS}" opacity="{.85 - i * .12:.2f}"/>'
        b += f'<rect x="{mx + 14}" y="{y}" width="{ask}" height="24" fill="{EMBER}" opacity="{.85 - i * .12:.2f}"/>'
    b += text(mx - 80, top - 18, "bids", 20, MOSS, "middle") + text(mx + 80, top - 18, "asks", 20, EMBER, "middle")
    ay = base - 140
    route_ok = f"M{agents[0][1]},{ay} L{agents[1][1]},{ay} L{agents[2][1]},{ay} L{mx},{top + 13}"
    route_no = f"M{agents[0][1]},{ay} L{agents[1][1]},{ay}"
    T = 9
    b += f'<path d="{route_ok}" fill="none" stroke="{SOUL}" stroke-opacity=".14" stroke-width="5" stroke-linejoin="round"/>'
    b += (f'<circle r="6" fill="{INK}" filter="url(#light)" opacity="0">'
          f'<animateMotion dur="{T}s" repeatCount="indefinite" path="{route_ok}" keyPoints="0;1;1" keyTimes="0;.42;1" calcMode="linear"/>'
          f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.42;.43;1" dur="{T}s" repeatCount="indefinite"/></circle>')
    b += (f'<circle cx="{mx}" cy="{top + 13}" r="34" fill="url(#pool)" opacity="0">'
          f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;.41;.45;.58;1" dur="{T}s" repeatCount="indefinite"/></circle>')
    b += (f'<circle r="6" fill="{EMBER}" filter="url(#light)" opacity="0">'
          f'<animateMotion dur="{T}s" repeatCount="indefinite" path="{route_no}" keyPoints="0;0;1;1" keyTimes="0;.55;.72;1" calcMode="linear"/>'
          f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.55;.56;.72;.76;1" dur="{T}s" repeatCount="indefinite"/></circle>')
    b += (f'<circle cx="{agents[1][1]}" cy="{ay}" r="30" fill="{EMBER}" opacity="0">'
          f'<animate attributeName="opacity" values="0;0;.5;0;0" keyTimes="0;.71;.74;.86;1" dur="{T}s" repeatCount="indefinite"/></circle>')
    cap = 360
    b += (f'<g opacity="0">{text(cap, base - 196, "Order passes the risk gate and fills", 22, MOSS, "middle")}'
          f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.04;.5;.53;1" dur="{T}s" repeatCount="indefinite"/></g>'
          f'<g opacity="0">{text(cap, base - 196, "Next order breaks a position limit: rejected", 22, EMBER, "middle")}'
          f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.54;.57;.95;1" dur="{T}s" repeatCount="indefinite"/></g>')
    b += text(1140, base + 32, "3,540 real orders replayed", 20, DIM, "end")
    write("chamber-trading-desk.svg", svg(H, b, "Agentic Trading Desk: an order passes the risk gate and fills; the next is rejected"))


# ── relics: one number carved large, the rest set beside it ──────────────────────────────────────
def relics():
    H = 600
    b = hollow(20, 10, W - 20, H - 10, 51, FIELD["relics"])
    b += f'<circle cx="250" cy="290" r="200" fill="url(#pool)" opacity=".35" class="fl"/>'
    b += text(64, 320, "1854", 190, INK, weight="600")
    b += text(72, 384, "LeetCode, max rating.", 24, LANTERN)
    b += text(72, 422, "750+ problems solved.", 22, DIM)
    rows = [("Codeforces Expert", "max rating 1605"),
            ("3★ CodeChef", "max rating 1621"),
            ("Amazon ML Summer School", "top 1.8% of 1.6 lakh+ applicants, 2026"),
            ("Google Big Code", "top 1,500 of 15,000+ globally, 2026"),
            ("Meta × PyTorch OpenEnv", "hackathon grand finale, Bengaluru"),
            ("NIT Patna, CSE '27", "CGPA 8.17")]
    for i, (big, small) in enumerate(rows):
        y = 96 + i * 82
        b += text(640, y, big, 32, INK, weight="600") + text(642, y + 32, small, 21, DIM)
    b += spores(10, 40, W - 40, 100, H - 20, 52, (LANTERN, INK))
    write("relics.svg", svg(H, b, "Relics: LeetCode 1854, Codeforces Expert 1605, CodeChef 3 star, Amazon MLSS 2026, "
                                  "Google Big Code 2026, Meta PyTorch OpenEnv finalist, NIT Patna CGPA 8.17"))


# ── what I've done and what I carry ──────────────────────────────────────────────────────────────
LANG_COLORS = {"Python": SOUL, "JavaScript": LANTERN, "Go": MOSS, "C++": EMBER, "TypeScript": "#c9b8ff"}


def carried(langs, n_repos):
    H = 500
    b = hollow(20, 10, W - 20, H - 10, 61, FIELD["carry"])
    b += text(70, 104, "Quests completed", 30, INK, weight="600")
    for i, (role, org) in enumerate([("Machine Learning Engineer Intern", "Trialshopy"),
                                      ("Data Scientist Intern", "Prodigy Infotech")]):
        y = 158 + i * 72
        b += text(72, y, role, 23, INK) + text(72, y + 30, org, 20, DIM)
    b += text(72, 320, "Next quest: open. Send a raven below.", 22, LANTERN)
    b += text(640, 104, "Carried", 30, INK, weight="600")
    b += lines(642, 150, ["C++, Python, Go, JavaScript, SQL", "PyTorch, Hugging Face, scikit-learn",
                          "Django, MERN, FalkorDB, Docker, MCP", "Computer vision, NLP, affective",
                          "computing (EEG and eye-tracking)"], 22, INK, lead=1.5)
    # one segmented bar of real language bytes
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    total = sum(v for _, v in top) or 1
    x, y, width = 72, 398, W - 144
    for name, v in top:
        w = width * v / total
        c = LANG_COLORS.get(name, DIM)
        b += f'<rect x="{x:.1f}" y="{y}" width="{max(w - 3, 2):.1f}" height="16" fill="{c}"/>'
        if w > 70:
            b += text(x, y + 44, f"{name} {100 * v / total:.0f}%", 19, INK)
        x += w
    b += text(W - 72, y - 16, f"code by language across {n_repos} repos, refreshed daily", 18, DIM, "end")
    write("carried.svg", svg(H, b, "Quests completed and what I carry: experience, stack and languages"))


# ── the bottom of the cave: name returns, progress saved ────────────────────────────────────────
def rest():
    H = 380
    b = hollow(0, 0, W, H, 71, FIELD["rest"], roof=34, floor=4)
    b += text(W / 2, 262, "Suryansh Sharma", 150, STEP["rest"], "middle", weight="600")
    b += f'<path d="M0,{H} L0,{H - 70} C300,{H - 92} 900,{H - 80} {W},{H - 96} L{W},{H} Z" fill="{ROCK}"/>'
    b += f'<path d="M520,{H - 84} q70,-30 150,-6 L676,{H - 76} Z" fill="#141c2c"/>'
    b += wanderer(600, H - 118, 1.25, seated=True)
    b += spores(22, 380, 820, 80, H - 60, 72, (LANTERN, LANTERN, SOUL))
    b += text(W / 2, 74, "You rest by the lantern. Progress saved.", 24, INK, "middle")
    b += text(W / 2, 112, "Thank you for coming this deep.", 21, DIM, "middle", italic=True)
    write("rest.svg", svg(H, b, "You rest by the lantern. Progress saved."))


def main():
    ASSETS.mkdir(exist_ok=True)
    for old in ASSETS.glob("*.svg"):
        old.unlink()
    langs, n_repos = fetch_stats("--offline" in sys.argv)
    hero()
    chamber_raft()
    chamber_hive()
    chamber_desk()
    relics()
    carried(langs, n_repos)
    rest()


if __name__ == "__main__":
    main()

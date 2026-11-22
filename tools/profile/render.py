"""Renders the profile SVGs (Matrix theme) from tools/profile/data into assets/.

  python tools/profile/fetch.py    # needs GITHUB_TOKEN or PROFILE_TOKEN
  python tools/profile/render.py   # PREVIEW=1 also screenshots PNGs (Windows + Edge only)
"""
import json, math, random, datetime as dt, os, subprocess, tempfile, re, html
import viz

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "assets"))
G = dict(bg="#000000", bg2="#000a03", bg3="#001a07", hi="#c8ffbf", txt="#39ff6a", mid="#1fcf4c",
         dim="#147a2e", faint="#0b3d18", ghost="#06200d")
KATA = "0123456789ABCDEF"  # hex rain, no asian glyphs
BIN = "01"

CSS = """text{font-family:MX,'Cascadia Mono',Consolas,ui-monospace,monospace}
.tw{animation:tw 3s ease-in-out infinite}.fl{animation:fl 6s steps(1) infinite}.bl{animation:tw 1.2s steps(1) infinite}
.cur{animation:tw 1s steps(1) infinite}.pulse{animation:pu 2.4s ease-in-out infinite}
.beam{animation:be 3.5s ease-in-out infinite}
@keyframes tw{50%{opacity:.15}}@keyframes fl{0%,90%{opacity:1}93%{opacity:.15}}
@keyframes pu{50%{opacity:.35}}@keyframes be{50%{opacity:.45}}
@keyframes fall{from{transform:translateY(-260px)}to{transform:translateY(260px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}"""

DEFS = """<filter id="soft"><feGaussianBlur stdDeviation=".6"/></filter>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.2" result="b"/>
 <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="bigglow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/>
 <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="crt" x="0" y="0" width="100%" height="100%">
 <feColorMatrix in="SourceGraphic" values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0" result="r"/><feOffset in="r" dx="1" result="r2"/>
 <feColorMatrix in="SourceGraphic" values="0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1 0" result="gb"/><feOffset in="gb" dx="-.5" result="gb2"/>
 <feBlend in="r2" in2="gb2" mode="screen" result="ca"/>
 <feGaussianBlur in="ca" stdDeviation="1.4" result="b"/><feBlend in="ca" in2="b" mode="screen"/></filter>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1.5" fill="#000" opacity=".42"/></pattern>
<radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".85"/></radialGradient>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000"/><stop offset=".6" stop-color="#000a03"/><stop offset="1" stop-color="#001a07"/></linearGradient>
<linearGradient id="beamg" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#c8ffbf" stop-opacity=".9"/><stop offset="1" stop-color="#39ff6a" stop-opacity="0"/></linearGradient>
<linearGradient id="fog" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#39ff6a" stop-opacity="0"/><stop offset="1" stop-color="#39ff6a" stop-opacity=".10"/></linearGradient>
<radialGradient id="moon"><stop offset="0" stop-color="#39ff6a" stop-opacity=".35"/><stop offset="1" stop-color="#39ff6a" stop-opacity="0"/></radialGradient>"""


FONT = os.path.join(HERE, "fonts", "CascadiaMono.ttf")   # SIL Open Font License, see fonts/
_inst = {}


def font_css(chars):
    """Subset Cascadia Mono (regular + bold) to the glyphs used, embed as base64 WOFF."""
    import io, base64
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    from fontTools import subset
    css = ""
    for wt in (400, 700):
        if wt not in _inst:
            buf = io.BytesIO()
            instancer.instantiateVariableFont(TTFont(FONT), {"wght": wt}).save(buf)
            _inst[wt] = buf.getvalue()
        f = TTFont(io.BytesIO(_inst[wt]))
        opt = subset.Options()
        opt.layout_features = []
        opt.hinting = False
        sub = subset.Subsetter(opt)
        sub.populate(text=chars)
        sub.subset(f)
        # OFL: a modified (subset) font must not keep the Reserved Font Name
        nm = f["name"]
        nm.names = []
        style = "Bold" if wt == 700 else "Regular"
        for nid, val in ((1, "MX Mono"), (2, style), (4, f"MX Mono {style}"), (6, f"MXMono-{style}")):
            nm.setName(val, nid, 3, 1, 0x409)
        f.flavor = "woff"
        out = io.BytesIO()
        f.save(out)
        b64 = base64.b64encode(out.getvalue()).decode()
        css += f"@font-face{{font-family:MX;font-weight:{wt};src:url(data:font/woff;base64,{b64}) format('woff')}}"
    return css


def svg(w, h, body, title, crt=True, over="", hud=()):
    inner = "\n".join(body)
    g = '<g filter="url(#crt)">' if crt else "<g>"
    scan = '<rect width="100%" height="100%" fill="url(#scan)"/><rect width="100%" height="100%" fill="url(#vig)"/>' if crt else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<title>{html.escape(title)}</title><defs>{DEFS}<clipPath id="card"><rect width="{w}" height="{h}" rx="12"/></clipPath></defs>
<style>{CSS}</style>
<g clip-path="url(#card)"><rect width="100%" height="100%" fill="url(#bg)"/>{g}<rect width="100%" height="100%" fill-opacity="0"/>
{inner}
</g>{"".join(hud)}{scan}{over}</g>
</svg>'''


def esc(s):
    return html.escape(s, quote=False)


def stream(x, y0, n, rng, glyphs, size=13, step=None, head=True, color=G["txt"], dur=None, op=1.0):
    """One vertical rain stream; brightest glyph at the bottom (head)."""
    step = step or size + 2
    parts = []
    for i in range(n):
        k = i / max(1, n - 1)
        c = G["hi"] if (head and i == n - 1) else color
        a = (.12 + .88 * k ** 1.6) * op
        parts.append(f'<text x="{x:.1f}" y="{y0 + i * step:.1f}" fill="{c}" fill-opacity="{a:.2f}">{esc(rng.choice(glyphs))}</text>')
    g = "".join(parts)
    if dur:
        return (f'<g font-size="{size}" text-anchor="middle" style="animation:fall {dur:.1f}s linear {-rng.uniform(0, dur):.1f}s infinite">{g}</g>')
    return f'<g font-size="{size}" text-anchor="middle">{g}</g>'


# ------------------------------------------------------------------ data
def load():
    p = json.load(open("profile.json"))
    days = [(d, n) for d, n in p["days"] if d <= dt.date.today().isoformat()]
    return p, days


def streaks(days):
    cur = best = run = 0
    best_end = best_start = cur_start = None
    start = None
    for d, n in days:
        if n:
            run += 1
            start = start or d
            if run > best:
                best, best_start, best_end = run, start, d
        else:
            run, start = 0, None
    # current: allow today to be 0
    i = len(days) - 1
    if days[i][1] == 0:
        i -= 1
    while i >= 0 and days[i][1]:
        cur += 1
        cur_start = days[i][0]
        i -= 1
    return cur, cur_start, best, best_start, best_end


# --------------------------------------------------------- hero: city
def hero(cells, peak, kind="base", W=900, H=560):
    viz.W, viz.H = W, H
    rng = random.Random(7)
    t = dict(viz.THEMES["matrix"])
    wire = kind == "wire"
    if wire:
        t.update(wall_l="#000", wall_r="#000", ground="#000", ground_l="#000", ground_r="#000",
                 roofs=["#03200c", "#0b4d1e", "#119c3a", "#39ff6a"], wire="#1fcf4c", grid="#0f3d1a")
    city = viz.city(cells, peak, t, layout="districts", proj="iso_s" if H < 650 else "iso")
    meta = viz.city.meta
    tops = [c["top"] for c in cells if c.get("top")]
    skyline_y = min(y for _, y in tops)
    body = []

    # --- sky: digital rain that fades out before reaching the rooftops
    nrain = 0 if kind == "clean" else 46
    body.append(f'<mask id="skym"><linearGradient id="sm" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="#fff"/><stop offset="{(skyline_y + 40) / H:.2f}" stop-color="#fff" stop-opacity=".9"/>'
                f'<stop offset="{(skyline_y + 140) / H:.2f}" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                f'<rect width="{W}" height="{H}" fill="url(#sm)"/></mask>')
    rain = []
    for x in range(10, W, 17):
        if rng.random() > (.0 if kind == "clean" else .7):
            continue
        L = rng.randint(6, 18)
        y0 = rng.uniform(-120, skyline_y - 60)
        rain.append(stream(x, y0, L, rng, KATA, size=12, step=15, dur=rng.uniform(8, 18), op=rng.uniform(.12, .32), head=False, color=G["mid"]))
    body.append(f'<g mask="url(#skym)" filter="url(#soft)">{"".join(rain)}</g>')

    # --- a quiet "moon": a terminal-green disc with a cursor-block bite
    if kind in ("base", "hud", "wire"):
        body.append(f'<circle cx="{W - 120}" cy="120" r="90" fill="url(#moon)"/>'
                    f'<circle cx="{W - 120}" cy="120" r="30" fill="none" stroke="{G["txt"]}" stroke-width="1" opacity=".55"/>'
                    f'<rect x="{W - 132}" y="108" width="12" height="22" fill="{G["txt"]}" class="cur" opacity=".9"/>')

    # --- the city itself
    body += city

    # --- ground fog over the base
    body.append(f'<rect x="0" y="{skyline_y + 120:.0f}" width="{W}" height="{H}" fill="url(#fog)"/>')

    best = max((c for c in cells if c.get("top")), key=lambda c: c["n"])
    if kind in ("hud", "wire", "beam"):
        # uplink beam from the busiest day into the sky
        x, y = best["top"]
        body.append(f'<polygon points="{x - 5},{y} {x + 5},{y} {x + 1.5},110 {x - 1.5},110" fill="url(#beamg)" class="beam"/>')
        body.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{G["hi"]}" filter="url(#bigglow)" class="pulse"/>')
        body.append(f'<line x1="{x}" y1="112" x2="{x + 26}" y2="112" stroke="{G["mid"]}" stroke-width=".8"/>')
        peak_label = (f'<text x="{x + 32:.0f}" y="110" font-size="12" font-weight="700" fill="{G["hi"]}">peak · {best["n"]} commits</text>'
                      f'<text x="{x + 32:.0f}" y="126" font-size="10" fill="{G["mid"]}">{dt.date.fromisoformat(best["date"]).strftime("%b %d, %Y")}</text>')
    else:
        peak_label = ""
    if kind in ("hud", "wire"):
        # month labels floating over each district
        pt = meta["pt"]
        for (x0, y0, x1, y1), m in zip(meta["blocks"], meta["months"]):
            sx, sy = pt(x0 + .2, y1 + .9, 0)
            name = dt.date.fromisoformat(m + "-01").strftime("%b").upper()
            body.append(f'<text x="{sx:.0f}" y="{sy + 4:.0f}" font-size="10" font-weight="700" fill="{G["mid"]}" letter-spacing="1">{name}</text>')
        # today's building pulses
        today = [c for c in cells if c.get("top")][-1]
        x, y = today["top"]
        body.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="{G["hi"]}" class="pulse"/>'
                    f'<text x="{x + 8:.0f}" y="{y - 8:.0f}" font-size="9" fill="{G["mid"]}">latest</text>')

    tot = sum(c["n"] for c in cells)
    act = sum(1 for c in cells if c["n"])
    hud = [peak_label, f'<text x="32" y="46" font-size="20" font-weight="700" fill="{G["txt"]}" filter="url(#glow)">~/contribution-city</text>',
           f'<text x="32" y="70" font-size="12" fill="{G["mid"]}">{tot:,} commits · {act} active days · last 12 months</text>',
           f'<text x="32" y="{H - 28}" font-size="11" fill="{G["mid"]}">&gt; one building per day · one district per month<tspan fill="{G["txt"]}" class="cur"> █</tspan></text>']
    if kind in ("hud", "wire"):
        # terminal corner brackets
        for (x, y, dx, dy) in ((14, 14, 1, 1), (W - 14, 14, -1, 1), (14, H - 14, 1, -1), (W - 14, H - 14, -1, -1)):
            hud.append(f'<path d="M{x},{y + 18 * dy}V{y}H{x + 18 * dx}" fill="none" stroke="{G["mid"]}" stroke-width="1.5"/>')
        legend_x = W - 250
        hud.append(f'<text x="{legend_x}" y="{H - 28}" font-size="10" fill="{G["mid"]}">quiet</text>')
        for i, c in enumerate(t["roofs"]):
            hud.append(f'<rect x="{legend_x + 42 + i * 18}" y="{H - 38}" width="12" height="12" fill="{c}"/>')
        hud.append(f'<text x="{legend_x + 42 + 4 * 18 + 6}" y="{H - 28}" font-size="10" fill="{G["mid"]}">skyscraper</text>')
    return svg(W, H, body, "Contribution city", hud=hud)


# ------------------------------------------- minimal rain idea 1: commit rain
def commit_rain(cells, W=900, H=260):
    """Each column is a week. Stream length = commits that week. Head = most recent day."""
    rng = random.Random(11)
    weeks = {}
    for c in cells:
        weeks.setdefault(c["w"], []).append(c)
    wk = [weeks[k] for k in sorted(weeks)]
    mx = max(sum(d["n"] for d in w) for w in wk) or 1
    cw = (W - 80) / len(wk)
    body = []
    for i, w in enumerate(wk):
        s = sum(d["n"] for d in w)
        x = 40 + i * cw + cw / 2
        if s == 0:
            body.append(f'<text x="{x:.1f}" y="{H - 40}" font-size="11" text-anchor="middle" fill="{G["faint"]}">.</text>')
            continue
        L = max(1, round(1 + 14 * math.sqrt(s / mx)))
        body.append(stream(x, H - 40 - (L - 1) * 13, L, rng, BIN, size=11, step=13))
    body.append(f'<line x1="40" x2="{W - 40}" y1="{H - 30}" y2="{H - 30}" stroke="{G["faint"]}"/>')
    for i, w in enumerate(wk):
        d = dt.date.fromisoformat(w[0]["date"])
        if d.day <= 7:
            body.append(f'<text x="{40 + i * cw:.1f}" y="{H - 14}" font-size="9" fill="{G["dim"]}">{d.strftime("%b").lower()}</text>')
    body.append(f'<text x="32" y="36" font-size="12" fill="{G["mid"]}">$ git log --since="1 year" | rain</text>')
    return svg(W, H, body, "Commit rain", crt=False)


# ------------------------------------ minimal rain idea 2: binary heatmap
def binary_grid(cells, W=900, H=230):
    """The calendar printed as text: '.' for no commits, digits brighter as days get busier."""
    nw = max(c["w"] for c in cells) + 1
    cw = (W - 110) / nw
    shade = [G["faint"], G["dim"], G["mid"], G["txt"], G["hi"]]
    body = [f'<text x="32" y="36" font-size="12" fill="{G["mid"]}">$ cat ~/.contributions</text>']
    for i, lab in ((1, "mon"), (3, "wed"), (5, "fri")):
        body.append(f'<text x="32" y="{70 + i * 20}" font-size="10" fill="{G["dim"]}">{lab}</text>')
    for c in cells:
        x, y = 80 + c["w"] * cw + cw / 2, 70 + c["dow"] * 20
        ch = "·" if c["n"] == 0 else ("9" if c["n"] > 9 else str(c["n"]))
        f = ' filter="url(#glow)"' if c["lv"] == 4 else ""
        body.append(f'<text x="{x:.1f}" y="{y}" font-size="12" text-anchor="middle" fill="{shade[c["lv"]]}"{f}>{ch}</text>')
    return svg(W, H, body, "Binary heatmap", crt=False)


# ------------------------------------------- header: name resolving from rain
def name_banner(name="G-BRRZZN", sub="", W=900, H=130):
    rng = random.Random(3)
    body = []
    for x in range(10, W, 16):
        if rng.random() < .55:
            body.append(stream(x, rng.uniform(-40, 120), rng.randint(3, 9), rng, KATA, size=11, dur=rng.uniform(6, 13),
                               op=rng.uniform(.08, .22), head=False, color=G["mid"]))
    body.append(f'<text x="{W / 2}" y="{H / 2 + 16}" font-size="46" font-weight="800" text-anchor="middle" letter-spacing="10" '
                f'fill="{G["hi"]}">{name}</text>')
    if sub:
        body.append(f'<text x="{W / 2}" y="142" font-size="12" text-anchor="middle" fill="{G["mid"]}" letter-spacing="2">'
                    f'&gt; {esc(sub)}<tspan class="cur" fill="{G["txt"]}"> █</tspan></text>')
    return svg(W, H, body, name)


# ---------------------------------------------------------- cards
def streak_card(p, days, W=440, H=200):
    cur, cs, best, bs, be = streaks(days)
    tot = sum(n for _, n in days)
    f = lambda d: dt.date.fromisoformat(d).strftime("%b %d, %Y") if d else "-"
    since = f(days[0][0])
    cols = [("total", f"{tot:,}", f"since {since}"),
            ("current_streak", f"{cur}d", f"{f(cs)} → today" if cur else "start one today"),
            ("longest_streak", f"{best}d", f"{f(bs)[:6]} → {f(be)}")]
    body = [f'<text x="24" y="34" font-size="13" font-weight="700" fill="{G["txt"]}">&gt; streak --stats</text>']
    for i, (k, v, s) in enumerate(cols):
        x = 24 + i * 136
        big = G["hi"] if i == 1 else G["txt"]
        body.append(f'<text x="{x}" y="72" font-size="10" fill="{G["dim"]}">{k}</text>'
                    f'<text x="{x}" y="112" font-size="34" font-weight="800" fill="{big}"{" filter=" + chr(34) + "url(#glow)" + chr(34) if i == 1 else ""}>{v}</text>'
                    f'<text x="{x}" y="136" font-size="9.5" fill="{G["mid"]}">{esc(s)}</text>')
        if i:
            body.append(f'<line x1="{x - 14}" x2="{x - 14}" y1="60" y2="146" stroke="{G["faint"]}"/>')
    # last 30 days as a tiny binary strip
    last = days[-30:]
    shades = ["#0b4d1e", "#119c3a", "#39ff6a", "#c8ffbf"]
    nz = sorted(n for _, n in last if n) or [1]
    q = [nz[int(len(nz) * f)] for f in (.25, .5, .75)]
    cw = (W - 48) / 30
    body.append(f'<text x="24" y="160" font-size="9" fill="{G["dim"]}">last 30 days</text>')
    for i, (_, n) in enumerate(last):
        col = "#06200d" if n == 0 else shades[sum(n > t for t in q)]
        body.append(f'<rect x="{24 + i * cw:.1f}" y="168" width="{cw - 2.5:.1f}" height="{cw - 2.5:.1f}" rx="1.5" fill="{col}"/>')
    return svg(W, H, body, "Streak", crt=False)


def avatar(W=460, H=460):
    rng = random.Random(21)
    body = []
    for x in range(8, W, 16):
        if rng.random() < .7:
            body.append(stream(x, rng.uniform(-60, 300), rng.randint(5, 14), rng, KATA, size=12, op=rng.uniform(.10, .28),
                               head=False, color=G["mid"]))
    body.append(f'<circle cx="{W / 2}" cy="{H / 2}" r="150" fill="#000" opacity=".7"/>')
    body.append(f'<text x="{W / 2}" y="{H / 2 + 72}" font-size="220" font-weight="800" text-anchor="middle" fill="{G["hi"]}" filter="url(#glow)">G</text>')
    return svg(W, H, body, "G").replace('rx="12"', 'rx="0"')


# ------------------------------------------------------------ render
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def shoot(src, png, w, h):
    prof = os.path.join(tempfile.gettempdir(), f"edgeshot-{os.getpid()}-{abs(hash(png))}")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={prof}",
                    f"--window-size={w},{h}", "--default-background-color=00000000", f"--screenshot={os.path.abspath(png)}",
                    "file:///" + os.path.abspath(src).replace("\\", "/")], check=True, capture_output=True, timeout=90)
    import time
    for _ in range(40):
        if os.path.exists(png):
            return
        time.sleep(.25)


def write(name, s):
    chars = html.unescape("".join(re.findall(r">([^<]+)<", s))) + " "
    s = s.replace("<style>", "<style>" + font_css(chars), 1)
    path = f"{OUT}/{name}.svg"
    open(path, "w", encoding="utf-8").write(s)
    w, h = map(int, re.search(r'width="(\d+)" height="(\d+)"', s).groups())
    if not os.environ.get("PREVIEW"):
        return
    png = f"{OUT}/{name}.png"
    if os.path.exists(png):
        os.remove(png)
    shoot(path, png, w, h)
    if not os.path.exists(png):
        shoot(path, png, w, h)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.chdir(DATA)
    p, alldays = load()
    json.dump(alldays[-365:], open("data.json", "w"))
    cells, peak = viz.load()
    import langs
    write("banner", name_banner())
    write("city", hero([dict(c) for c in cells], peak, "hud"))
    write("card-langs", svg(440, 200, langs.treemap(langs.top6()), "Most used languages", crt=False))
    write("card-streak", streak_card(p, alldays))
    print("rendered into", OUT)

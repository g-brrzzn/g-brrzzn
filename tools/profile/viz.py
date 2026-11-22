"""Laboratório de visualizações do calendário de contribuições.

Gera vários SVGs (temas x estilos x filtros) a partir de data.json.
  python viz.py            -> out/*.svg  (depois: python shoot.py para PNGs)
"""
import json, math, random, datetime as dt, os

W, H = 900, 630

# ---------------------------------------------------------------- temas
THEMES = {
    "sunset": dict(
        bg=["#140f24", "#3b1d3a", "#5b2a2a"], wall_l="#2a1d3a", wall_r="#1c1428",
        roofs=["#7a2e1f", "#c2410c", "#f97316", "#fdba74"], win=["#ffd166", "#ffb347"],
        ground="#1a1424", ground_l="#24182f", ground_r="#150f1e", grid="#2a1f38",
        text="#fde7c7", text2="#f9a66c", muted="#b48a9a", star="#fde7c7", orb=("#ffb347", "#ff6b35")),
    # paleta do tema "Neon city" (Daemon 2.0) ativo no app
    "neon": dict(
        bg=["#0d070b", "#160b11", "#331319"], wall_l="#210e15", wall_r="#160b11",
        roofs=["#5a1a3a", "#e455ae", "#fb3048", "#fdf500"], win=["#5df4fe", "#f3e500"],
        ground="#160b11", ground_l="#331319", ground_r="#210e15", grid="#fb304844",
        text="#5df4fe", text2="#ff7a85", muted="#a58fd8", star="#5df4fe", orb=("#fb3048", "#e455ae")),
    "matrix": dict(
        bg=["#000000", "#000a03", "#001a07"], wall_l="#03200c", wall_r="#011207",
        roofs=["#0b4d1e", "#119c3a", "#2bd65a", "#c8ffbf"], win=["#39ff6a", "#1fcf4c"],
        ground="#010d04", ground_l="#02200a", ground_r="#011306", grid="#0f3d1a",
        text="#39ff6a", text2="#1fcf4c", muted="#147a2e", star="#39ff6a", orb=("#39ff6a", "#003b12")),
    "blueprint": dict(
        bg=["#0a2340", "#0b2a4a", "#0d3157"], wall_l="#0b2a4a", wall_r="#0a2645",
        roofs=["#12395f", "#1a4d7d", "#27679f", "#cfe8ff"], win=["#cfe8ff", "#9cc9f0"],
        ground="#0b2a4a", ground_l="#0d3157", ground_r="#0a2645", grid="#2a5b8a",
        text="#eaf4ff", text2="#9cc9f0", muted="#5f8fbf", star="#cfe8ff", orb=("#cfe8ff", "#0b2a4a"),
        wire="#cfe8ff"),
    "paper": dict(
        bg=["#f4ecdc", "#efe5d1", "#e8dcc4"], wall_l="#3a3532", wall_r="#24201e",
        roofs=["#6b625b", "#4a433e", "#2a2522", "#c8102e"], win=["#f4ecdc", "#e8dcc4"],
        ground="#e2d5bb", ground_l="#cbbd9f", ground_r="#b8a988", grid="#cdbf9f",
        text="#1d1a18", text2="#c8102e", muted="#7a6f62", star=None, orb=("#c8102e", "#f4ecdc")),
}

# ------------------------------------------------------------- projeções
# base: vetor de tela para +1 semana (ex), +1 dia (ey) e escala de altura (ez)
PROJ = {
    "iso":   dict(ex=(12.5, 6.25), ey=(-12.5, 6.25), ez=1.0, o=(170, 215)),
    "iso_s": dict(ex=(11.0, 5.5), ey=(-11.0, 5.5), ez=0.85, o=(170, 215)),
    "steep": dict(ex=(12.5, 9.5), ey=(-12.5, 9.5), ez=0.75, o=(170, 175)),
    "low":   dict(ex=(13.5, 3.2), ey=(-9.0, 5.5), ez=1.15, o=(110, 300)),
    "front": dict(ex=(14.5, 0.0), ey=(-5.5, 7.0), ez=1.0, o=(110, 380)),
}


def load():
    days = json.load(open("data.json"))
    first = dt.date.fromisoformat(days[0][0])
    first -= dt.timedelta(days=(first.weekday() + 1) % 7)
    cells = []
    for date, n in days:
        d = dt.date.fromisoformat(date)
        cells.append(dict(date=date, n=n, w=(d - first).days // 7, dow=(d.weekday() + 1) % 7))
    nz = sorted(c["n"] for c in cells if c["n"])
    q = [nz[int(len(nz) * f)] for f in (.25, .5, .75)]
    peak = max(nz)
    for c in cells:
        c["lv"] = 0 if c["n"] == 0 else 1 + sum(c["n"] > t for t in q)  # 0..4
    return cells, peak


def P(pts):
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"


def poly(pts, fill, extra=""):
    return f'<path d="{P(pts)}" fill="{fill}"{extra}/>'


def bg_defs(t):
    s = t["bg"]
    return (f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{s[0]}"/>'
            f'<stop offset=".65" stop-color="{s[1]}"/><stop offset="1" stop-color="{s[2]}"/></linearGradient>'
            f'<radialGradient id="orb"><stop offset="0" stop-color="{t["orb"][0]}" stop-opacity=".9"/>'
            f'<stop offset="1" stop-color="{t["orb"][1]}" stop-opacity="0"/></radialGradient>')


def sky(t, rng, region=(480, 30, 870, 200), orb=(800, 150, 55)):
    out = []
    if t.get("star"):
        x0, y0, x1, y1 = region
        for i in range(55):
            out.append(f'<circle cx="{rng.uniform(x0, x1):.0f}" cy="{rng.uniform(y0, y1):.0f}" '
                       f'r="{rng.choice((0.7, 1, 1.3))}" fill="{t["star"]}" opacity="{rng.uniform(.4, 1):.2f}"'
                       f'{' class="tw"' if i % 3 == 0 else ""}/>')
    if orb:
        out.append(f'<circle cx="{orb[0]}" cy="{orb[1]}" r="{orb[2]}" fill="url(#orb)"/>')
    return out


# ---------------------------------------------------------- estilo: cidade
def city(cells, peak, t, proj="iso", base=True, gap=0.12, seed=1, layout="strip"):
    pj = PROJ[proj]
    (exx, exy), (eyx, eyy), ez = pj["ex"], pj["ey"], pj["ez"]
    rng = random.Random(seed)
    wire = t.get("wire")
    stroke = f' stroke="{wire}" stroke-width=".6" stroke-linejoin="round"' if wire else ""

    # posição de cada célula no grid do mundo (gx, gy) e "quadras" (blocos de base)
    blocks = []
    months = []
    if layout == "districts":   # 12 bairros = 12 meses, em 4x3
        months = sorted({c["date"][:7] for c in cells})[-12:]
        for c in cells:
            if c["date"][:7] not in months:
                c["gx"] = None; continue
            m = months.index(c["date"][:7])
            d = dt.date.fromisoformat(c["date"])
            first = d.replace(day=1)
            col = (d.day - 1 + (first.weekday() + 1) % 7) // 7
            bx, by = (m % 4) * 7.6, (m // 4) * 8.6
            c["gx"], c["gy"] = bx + col, by + c["dow"]
        for m in range(len(months)):
            bx, by = (m % 4) * 7.6, (m // 4) * 8.6
            blocks.append((bx - .3, by - .3, bx + 6.3, by + 7.3))
    else:
        for c in cells:
            c["gx"], c["gy"] = c["w"], c["dow"]
    act = [c for c in cells if c["gx"] is not None]
    GX = max(c["gx"] for c in act) + 1
    GY = max(c["gy"] for c in act) + 1
    th = 22

    # centraliza automaticamente na tela
    corners = [(x, y, z) for x in (-0.6, GX + .6) for y in (-0.6, GY + .6) for z in (-th, 0)]
    raw = [(x * exx + y * eyx, x * exy + y * eyy - z * ez) for x, y, z in corners]
    minx, maxx = min(p[0] for p in raw), max(p[0] for p in raw)
    miny, maxy = min(p[1] for p in raw) - 120 * ez, max(p[1] for p in raw)
    ox = (W - (maxx - minx)) / 2 - minx
    oy = 110 + (H - 130 - (maxy - miny)) / 2 - miny

    def pt(w, d, z=0.0):
        return (ox + w * exx + d * eyx, oy + w * exy + d * eyy - z * ez)

    out = []
    if base:
        g = [(-0.6, -0.6), (GX + 0.6, -0.6), (GX + 0.6, GY + .6), (-0.6, GY + .6)]
        out += box_faces(pt, g, -th, 0, t["ground_l"], t["ground_r"], t["ground"], stroke)
        if layout == "districts":
            for x0, y0, x1, y1 in blocks:
                out += box_faces(pt, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0, 3,
                                 t["ground_l"], t["ground_r"], t["grid"] if not t["grid"].endswith("44") else t["ground_l"], stroke)
        else:
            for w in range(GX + 1):
                a, b = pt(w - gap / 2, -0.5), pt(w - gap / 2, GY + .5)
                out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{t["grid"]}" stroke-width=".5"/>')
            for d in range(GY + 1):
                a, b = pt(-0.5, d - gap / 2), pt(GX + 0.5, d - gap / 2)
                out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{t["grid"]}" stroke-width=".5"/>')

    z0 = 3 if layout == "districts" else 0
    order = sorted(act, key=lambda c: (pt(c["gx"] + .5, c["gy"] + .5)[1], pt(c["gx"] + .5, c["gy"] + .5)[0] * (1 if eyx < 0 else -1)))
    for c in order:
        w0, d0 = c["gx"] + gap / 2, c["gy"] + gap / 2
        w1, d1 = c["gx"] + 1 - gap / 2, c["gy"] + 1 - gap / 2
        fp = [(w0, d0), (w1, d0), (w1, d1), (w0, d1)]
        if c["n"] == 0:
            if not base:
                out.append(poly([pt(*p) for p in fp], t["ground"], f' stroke="{t["grid"]}" stroke-width=".5"'))
            continue
        h = 6 + 114 * math.sqrt(c["n"] / peak)
        out += box_faces(pt, fp, z0, z0 + h, t["wall_l"], t["wall_r"], t["roofs"][c["lv"] - 1], stroke,
                         windows=(rng, t["win"]))
        c["top"] = pt(c["gx"] + .5, c["gy"] + .5, z0 + h)
    city.meta = dict(pt=pt, blocks=blocks, months=months)
    return out


def box_faces(pt, fp, z0, z1, cl, cr, ctop, stroke="", windows=None):
    """Desenha as faces laterais visíveis + topo de um prisma com base fp (4 cantos, anti-horário)."""
    out = []
    faces = []
    for i in range(4):
        a, b = fp[i], fp[(i + 1) % 4]
        A, B = pt(*a, z0), pt(*b, z0)
        # visível se, percorrendo a base no sentido do polígono, a aresta vai para a esquerda na tela
        # (a face "olha" para baixo/câmera). Testado empiricamente para as projeções acima.
        mid_out = ((a[0] + b[0]) / 2 - (fp[0][0] + fp[2][0]) / 2, (a[1] + b[1]) / 2 - (fp[0][1] + fp[2][1]) / 2)
        sx = pt(mid_out[0], mid_out[1])[1] - pt(0, 0)[1]
        if sx > 0.01:  # normal aponta para baixo na tela => voltada para a câmera
            faces.append((a, b, A, B))
    for a, b, A, B in faces:
        col = cl if B[0] > A[0] else cr  # face cuja aresta vai à direita = esquerda clara
        At, Bt = pt(*a, z1), pt(*b, z1)
        out.append(poly([A, B, Bt, At], col, stroke))
        if windows and z1 - z0 > 14:
            rng, wc = windows
            lit = wc[0] if col == cl else wc[1]
            rows = int((z1 - z0 - 8) // 8)
            for r in range(rows):
                v = z0 + 6 + r * 8
                for u0 in (.2, .6):
                    if rng.random() > .5:
                        continue
                    u1 = u0 + .22
                    def q(u, dz):
                        x = a[0] + (b[0] - a[0]) * u; y = a[1] + (b[1] - a[1]) * u
                        return pt(x, y, v + dz)
                    fl = ' class="fl"' if rng.random() < .04 else ""
                    out.append(poly([q(u0, 0), q(u1, 0), q(u1, 3), q(u0, 3)], lit, fl))
    out.append(poly([pt(*p, z1) for p in fp], ctop, stroke))
    return out


# ------------------------------------------------- estilo: skyline frontal
def skyline(cells, peak, t, seed=2):
    rng = random.Random(seed)
    weeks = {}
    for c in cells:
        weeks[c["w"]] = weeks.get(c["w"], 0) + c["n"]
    wk = [weeks[k] for k in sorted(weeks)]
    mx = max(wk) or 1
    horizon, x0, bw = 500, 40, (W - 80) / len(wk)
    out = sky(t, rng, region=(30, 110, 870, 330), orb=(700, horizon - 30, 120))
    # camada de fundo (silhueta)
    back = []
    for i, s in enumerate(wk):
        h = 30 + 170 * math.sqrt(wk[(i * 7 + 3) % len(wk)] / mx) * .8
        back.append((x0 + i * bw, horizon - h))
    pts = [(x0, horizon)] + [p for i, (x, y) in enumerate(back) for p in ((x, y), (x + bw, y))] + [(x0 + len(wk) * bw, horizon)]
    out.append(poly(pts, t["wall_r"], ' opacity=".55"'))
    front = []
    for i, s in enumerate(wk):
        if s == 0:
            continue
        h = 10 + 330 * math.sqrt(s / mx)
        x, w_ = x0 + i * bw + 1, bw - 2
        lv = min(3, int(4 * s / mx))
        g = [poly([(x, horizon), (x + w_, horizon), (x + w_, horizon - h), (x, horizon - h)], t["wall_l"])]
        g.append(f'<rect x="{x:.1f}" y="{horizon - h:.1f}" width="{w_:.1f}" height="2.5" fill="{t["roofs"][lv]}"/>')
        if h > 60 and rng.random() < .35:
            g.append(f'<rect x="{x + w_ / 2 - .6:.1f}" y="{horizon - h - 14:.1f}" width="1.2" height="14" fill="{t["wall_l"]}"/>'
                     f'<circle cx="{x + w_ / 2:.1f}" cy="{horizon - h - 14:.1f}" r="1.6" fill="{t["roofs"][3]}" class="bl"/>')
        for r in range(int((h - 10) // 7)):
            for cx in (x + 2.5, x + w_ - 5):
                if rng.random() < .45:
                    g.append(f'<rect x="{cx:.1f}" y="{horizon - h + 6 + r * 7:.1f}" width="2.5" height="3" fill="{t["win"][r % 2]}"/>')
        front.append("".join(g))
    out += front
    # reflexo na água
    out.append(f'<rect x="0" y="{horizon}" width="{W}" height="{H - horizon}" fill="{t["bg"][0]}" opacity=".85"/>')
    out.append(f'<g transform="translate(0,{2 * horizon}) scale(1,-1)" opacity=".28" filter="url(#ripple)">{"".join(front)}</g>')
    for i in range(14):
        y = horizon + 6 + i * i * .9
        out.append(f'<line x1="{rng.uniform(40, 400):.0f}" x2="{rng.uniform(500, 860):.0f}" y1="{y:.0f}" y2="{y:.0f}" stroke="{t["muted"]}" stroke-width=".6" opacity=".35"/>')
    out.append(f'<line x1="0" x2="{W}" y1="{horizon}" y2="{horizon}" stroke="{t["roofs"][2]}" stroke-width="1" opacity=".7"/>')
    return out


# -------------------------------------------- estilo: relevo synthwave
def terrain(cells, peak, t, seed=3):
    grid = [[0.0] * 7 for _ in range(max(c["w"] for c in cells) + 1)]
    for c in cells:
        grid[c["w"]][c["dow"]] = math.sqrt(c["n"] / peak)
    nw = len(grid)
    rows = 25
    horizon = 300
    out = [f'<circle cx="{W / 2}" cy="{horizon - 10}" r="120" fill="url(#sunstripe)"/>',
           f'<circle cx="{W / 2}" cy="{horizon - 10}" r="190" fill="url(#orb)" opacity=".35"/>']
    rng = random.Random(seed)
    out += sky(t, rng, region=(20, 40, 880, 220), orb=None)

    def height(wf, df):
        w0, d0 = min(int(wf), nw - 2), min(int(df), 5)
        fw, fd = wf - w0, df - d0
        a = grid[w0][d0] * (1 - fw) + grid[w0 + 1][d0] * fw
        b = grid[w0][d0 + 1] * (1 - fw) + grid[w0 + 1][d0 + 1] * fw
        return a * (1 - fd) + b * fd

    for r in range(rows - 1, -1, -1):  # de trás para frente
        z = r / (rows - 1)                       # 0 = perto, 1 = longe
        persp = 1 / (1 + z * 3.2)
        y = horizon + 300 * persp
        spread = 1250 * persp
        df = 6 * (1 - z)
        pts = []
        for i in range(161):
            wf = (nw - 1) * i / 160
            x = W / 2 + (i / 160 - .5) * spread
            hh = height(wf, df) * 170 * persp
            pts.append((x, y - hh))
        d = "M" + " L".join(f"{x:.1f},{yy:.1f}" for x, yy in pts)
        out.append(f'<path d="{d} L{pts[-1][0]:.1f},{H} L{pts[0][0]:.1f},{H} Z" fill="{t["bg"][0]}"/>')
        out.append(f'<path d="{d}" fill="none" stroke="{t["roofs"][2] if r % 4 else t["roofs"][3]}" stroke-width="{.6 + 1.2 * persp:.2f}" opacity="{.35 + .65 * persp:.2f}"/>')
    return out


# ---------------------------------------------------- estilo: radial
def radial(cells, peak, t):
    cx, cy, r0, rl = W / 2 + 120, H / 2 + 10, 95, 170
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r0 + rl + 8}" fill="none" stroke="{t["grid"]}" stroke-width=".6"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{r0 - 6}" fill="none" stroke="{t["grid"]}" stroke-width=".6"/>']
    n = len(cells)
    for i, c in enumerate(cells):
        a = -math.pi / 2 + 2 * math.pi * i / n
        L = 3 if c["n"] == 0 else 6 + rl * math.sqrt(c["n"] / peak)
        col = t["grid"] if c["n"] == 0 else t["roofs"][c["lv"] - 1]
        x1, y1 = cx + r0 * math.cos(a), cy + r0 * math.sin(a)
        x2, y2 = cx + (r0 + L) * math.cos(a), cy + (r0 + L) * math.sin(a)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="1.5" stroke-linecap="round"/>')
        if c["date"].endswith("-01"):
            m = dt.date.fromisoformat(c["date"]).strftime("%b").lower()
            lx, ly = cx + (r0 - 20) * math.cos(a), cy + (r0 - 20) * math.sin(a)
            out.append(f'<text x="{lx:.1f}" y="{ly + 4:.1f}" font-size="10" text-anchor="middle" fill="{t["muted"]}">{m}</text>')
    tot = sum(c["n"] for c in cells)
    out.append(f'<text x="{cx}" y="{cy + 2}" font-size="26" font-weight="700" text-anchor="middle" fill="{t["text"]}">{tot}</text>')
    out.append(f'<text x="{cx}" y="{cy + 22}" font-size="11" text-anchor="middle" fill="{t["muted"]}">commits / ano</text>')
    return out


# ------------------------------------------------ estilo: matrix rain
def rain(cells, peak, t, seed=4):
    rng = random.Random(seed)
    glyphs = "01アイウエオカキクケコサシスセソ/$#%*+=ZXQ"
    nw = max(c["w"] for c in cells) + 1
    cw, top = (W - 60) / nw, 330
    out = []
    # chuva de fundo animada
    for col in range(nw):
        x = 30 + col * cw + cw / 2
        L = rng.randint(6, 22)
        y0 = rng.uniform(-200, 250)
        s = "".join(f'<tspan x="{x:.1f}" dy="15">{rng.choice(glyphs)}</tspan>' for _ in range(L))
        dur = rng.uniform(4, 11)
        out.append(f'<text y="{y0:.0f}" font-size="12" text-anchor="middle" fill="{t["text"]}" opacity="{rng.uniform(.15, .45):.2f}" '
                   f'style="animation:drop {dur:.1f}s linear {-rng.uniform(0, dur):.1f}s infinite">{s}</text>')
    # o calendário em glifos
    for c in cells:
        x = 30 + c["w"] * cw + cw / 2
        y = top + c["dow"] * 32
        if c["n"] == 0:
            out.append(f'<text x="{x:.1f}" y="{y}" font-size="13" text-anchor="middle" fill="{t["grid"]}">·</text>')
            continue
        ch = str(c["n"]) if c["n"] < 10 else rng.choice("アカサタナハマヤラワ")
        col = t["roofs"][c["lv"] - 1]
        glow = ' filter="url(#glow)"' if c["lv"] == 4 else ""
        out.append(f'<text x="{x:.1f}" y="{y}" font-size="{12 + 3 * c["lv"]}" font-weight="700" text-anchor="middle" fill="{col}"{glow}>{ch}</text>')
    return out


# ------------------------------------------------ estilo: constelação
def constellation(cells, peak, t, seed=5):
    """Galáxia: os 365 dias numa espiral de 3 voltas, inclinada como um disco."""
    rng = random.Random(seed)
    cx, cy = W / 2 + 90, H / 2 + 30
    n = len(cells)
    out = sky(t, rng, region=(10, 10, 890, 620), orb=None)
    out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="70" ry="38" fill="url(#orb)" opacity=".7"/>')
    pts = []
    for i, c in enumerate(cells):
        th = i / n * 3 * 2 * math.pi + .4
        r = 35 + 235 * i / n
        x = cx + r * math.cos(th) + rng.uniform(-4, 4)
        y = cy + r * math.sin(th) * .5 + rng.uniform(-3, 3)
        pts.append((x, y, c))
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
    out.append(f'<path d="{d}" fill="none" stroke="{t["muted"]}" stroke-width="7" opacity=".08"/>')
    out.append(f'<path d="{d}" fill="none" stroke="{t["muted"]}" stroke-width=".5" opacity=".35"/>')
    for x, y, c in pts:
        if not c["n"]:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r=".7" fill="{t["muted"]}" opacity=".5"/>')
            continue
        r = 1.3 + 5.5 * math.sqrt(c["n"] / peak)
        col = t["roofs"][c["lv"] - 1]
        tw = ' class="tw"' if c["lv"] == 4 else ""
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 2.8:.1f}" fill="{col}" opacity=".13"/>'
                   f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}"{tw}/>')
    return out


# ------------------------------------------------------------ filtros
FILTER_DEFS = """
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/>
 <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="ripple"><feTurbulence type="fractalNoise" baseFrequency="0.01 0.18" numOctaves="1" seed="3"/>
 <feDisplacementMap in="SourceGraphic" scale="9"/></filter>
<filter id="bloom" x="0" y="0" width="100%" height="100%"><feGaussianBlur in="SourceGraphic" stdDeviation="4" result="b"/>
 <feBlend in="SourceGraphic" in2="b" mode="screen"/></filter>
<filter id="crt" x="0" y="0" width="100%" height="100%">
 <feColorMatrix in="SourceGraphic" values="1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0" result="r"/><feOffset in="r" dx="2" result="r2"/>
 <feColorMatrix in="SourceGraphic" values="0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1 0" result="gb"/><feOffset in="gb" dx="-1" result="gb2"/>
 <feBlend in="r2" in2="gb2" mode="screen" result="ca"/>
 <feGaussianBlur in="ca" stdDeviation="3" result="b"/><feBlend in="ca" in2="b" mode="screen"/></filter>
<filter id="pixel" x="0" y="0" width="100%" height="100%">
 <feFlood x="2" y="2" width="1" height="1"/><feComposite width="5" height="5"/><feTile result="t"/>
 <feComposite in="SourceGraphic" in2="t" operator="in"/><feMorphology operator="dilate" radius="2.5" result="px"/>
 <feComponentTransfer in="px"><feFuncR type="discrete" tableValues="0 .07 .15 .25 .4 .6 .8 1"/>
 <feFuncG type="discrete" tableValues="0 .07 .15 .25 .4 .6 .8 1"/><feFuncB type="discrete" tableValues="0 .07 .15 .25 .4 .6 .8 1"/></feComponentTransfer></filter>
<filter id="pixelbig" x="0" y="0" width="100%" height="100%">
 <feFlood x="4" y="4" width="1" height="1"/><feComposite width="9" height="9"/><feTile result="t"/>
 <feComposite in="SourceGraphic" in2="t" operator="in"/><feMorphology operator="dilate" radius="4.5"/></filter>
<filter id="ink" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" result="n"/>
 <feDisplacementMap in="SourceGraphic" in2="n" scale="2.5" result="d"/>
 <feColorMatrix in="n" type="saturate" values="0" result="g"/><feComponentTransfer in="g" result="g2"><feFuncA type="linear" slope=".12"/></feComponentTransfer>
 <feBlend in="d" in2="g2" mode="multiply"/></filter>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1.6" fill="#000" opacity=".45"/></pattern>
<radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".85"/></radialGradient>
<linearGradient id="sunstripe" x1="0" y1="0" x2="0" y2="1">
 <stop offset="0" stop-color="{a}"/><stop offset=".55" stop-color="{b}"/><stop offset=".55" stop-color="{b}" stop-opacity="0"/>
 <stop offset=".62" stop-color="{b}" stop-opacity="0"/><stop offset=".62" stop-color="{b}"/><stop offset=".7" stop-color="{b}"/>
 <stop offset=".7" stop-color="{b}" stop-opacity="0"/><stop offset=".78" stop-color="{b}" stop-opacity="0"/><stop offset=".78" stop-color="{b}"/>
 <stop offset=".84" stop-color="{b}"/><stop offset=".84" stop-color="{b}" stop-opacity="0"/><stop offset=".92" stop-color="{b}" stop-opacity="0"/>
 <stop offset=".92" stop-color="{b}"/><stop offset="1" stop-color="{b}"/></linearGradient>
"""

CSS = """text{font-family:'JetBrains Mono',ui-monospace,Consolas,monospace}
.tw{animation:tw 3s ease-in-out infinite}.fl{animation:fl 6s steps(1) infinite}.bl{animation:tw 1.4s steps(1) infinite}
@keyframes tw{50%{opacity:.2}}@keyframes fl{0%,90%{opacity:1}93%{opacity:.15}}
@keyframes drop{from{transform:translateY(-120px)}to{transform:translateY(520px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}"""


def compose(body, t, cells, title, flt=None, header=True):
    tot = sum(c["n"] for c in cells)
    best = max(cells, key=lambda c: c["n"])
    act = sum(1 for c in cells if c["n"])
    inner = "\n".join(body)
    wrap = f'<g filter="url(#{flt})">' if flt in ("crt", "pixel", "pixelbig", "bloom", "ink") else "<g>"
    if flt == "pixelcrt":
        wrap = '<g filter="url(#crt)"><g filter="url(#pixel)">'
    close = "</g></g>" if flt == "pixelcrt" else "</g>"
    hdr = ""
    if header:
        hdr = (f'<text x="30" y="44" font-size="20" font-weight="700" fill="{t["text"]}">{title}</text>'
               f'<text x="30" y="68" font-size="12" fill="{t["text2"]}">{tot:,} contribuições · {act} dias ativos</text>'
               f'<text x="30" y="86" font-size="12" fill="{t["muted"]}">pico: {best["date"]} ({best["n"]})</text>')
    over = ""
    if flt in ("crt", "pixelcrt"):
        over = '<rect width="100%" height="100%" fill="url(#scan)"/><rect width="100%" height="100%" fill="url(#vig)"/>'
    defs = FILTER_DEFS.replace("{a}", t["roofs"][3]).replace("{b}", t["roofs"][1])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<title>{title}</title><defs>{bg_defs(t)}{defs}<clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>
<style>{CSS}</style>
<g clip-path="url(#card)"><rect width="100%" height="100%" fill="url(#bg)"/>{wrap}<rect width="100%" height="100%" fill="#000" fill-opacity="0"/>
{inner}
{close}{over}{hdr}</g>
</svg>'''


VARIANTS = [
    # nome, estilo, tema, kwargs, filtro
    ("01-neon-districts", "city", "neon", dict(layout="districts"), None),
    ("02-neon-districts-crt", "city", "neon", dict(layout="districts"), "crt"),
    ("03-matrix-districts", "city", "matrix", dict(layout="districts"), "bloom"),
    ("04-matrix-districts-pixelcrt", "city", "matrix", dict(layout="districts", proj="steep"), "pixelcrt"),
    ("05-neon-strip-iso", "city", "neon", dict(proj="iso"), None),
    ("06-sunset-front", "city", "sunset", dict(proj="front"), None),
    ("07-blueprint-districts", "city", "blueprint", dict(layout="districts"), None),
    ("08-paper-districts-ink", "city", "paper", dict(layout="districts", proj="steep"), "ink"),
    ("09-neon-districts-pixel", "city", "neon", dict(layout="districts"), "pixelbig"),
    ("10-neon-skyline", "skyline", "neon", {}, "bloom"),
    ("11-sunset-skyline-crt", "skyline", "sunset", {}, "crt"),
    ("12-neon-terrain", "terrain", "neon", {}, "bloom"),
    ("13-matrix-terrain-crt", "terrain", "matrix", {}, "crt"),
    ("14-matrix-rain", "rain", "matrix", {}, "crt"),
    ("15-neon-rain", "rain", "neon", {}, "bloom"),
    ("16-neon-radial", "radial", "neon", {}, "bloom"),
    ("17-paper-radial", "radial", "paper", {}, "ink"),
    ("18-blueprint-galaxy", "constellation", "blueprint", {}, "bloom"),
    ("19-neon-galaxy", "constellation", "neon", {}, "bloom"),
    ("20-neon-terrain-pixelcrt", "terrain", "neon", {}, "pixelcrt"),
]

STYLES = dict(city=city, skyline=skyline, terrain=terrain, radial=radial, rain=rain, constellation=constellation)
TITLES = dict(city="~/cidade", skyline="~/skyline", terrain="~/relevo", radial="~/órbita", rain="~/matrix", constellation="~/galáxia")

if __name__ == "__main__":
    cells, peak = load()
    os.makedirs("out", exist_ok=True)
    for name, style, theme, kw, flt in VARIANTS:
        t = THEMES[theme]
        body = STYLES[style](cells, peak, t, **kw)
        if style == "city":
            body = sky(t, random.Random(9), region=(500, 30, 880, 190), orb=(810, 120, 55)) + body
        svg = compose(body, t, cells, TITLES[style], flt)
        open(f"out/{name}.svg", "w", encoding="utf-8").write(svg)
    print(len(VARIANTS), "variantes em out/")

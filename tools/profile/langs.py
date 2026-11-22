"""Most-used-languages card (the profile uses treemap); a few alternative layouts kept for reference.

Data: public, non-fork repos you own (same source as github-readme-stats), top 6,
percentages over those 6.
"""
import json, math
from render import svg, esc, G, write

SHADES = ["#c8ffbf", "#39ff6a", "#1fcf4c", "#119c3a", "#0b6b28", "#0b4d1e"]
W, H = 440, 200


def top6():
    nodes = json.load(open("pub.json"))["data"]["user"]["repositories"]["nodes"]
    L = {}
    for r in nodes:
        for e in r["languages"]["edges"]:
            L[e["node"]["name"]] = L.get(e["node"]["name"], 0) + e["size"]
    top = sorted(L.items(), key=lambda x: -x[1])[:6]
    t = sum(s for _, s in top)
    return [(n, 100 * s / t) for n, s in top]


def title(txt="most_used_languages"):
    return f'<text x="24" y="34" font-size="13" font-weight="700" fill="{G["txt"]}">&gt; {txt}</text>'


def ascii_bars(L):
    b = [title()]
    for i, (n, p) in enumerate(L):
        y = 64 + i * 22
        k = max(1, round(p / 100 * 22))
        b.append(f'<text x="24" y="{y}" font-size="12" fill="{G["mid"]}">{esc(n)}</text>'
                 f'<text x="124" y="{y}" font-size="12" fill="{G["txt"]}">{"█" * k}<tspan fill="{G["ghost"]}">{"█" * (22 - k)}</tspan></text>'
                 f'<text x="{W - 24}" y="{y}" font-size="12" text-anchor="end" fill="{G["dim"]}">{p:.2f}%</text>')
    return b


def stacked(L):
    """Like the readme-stats card: one segmented bar + 2-column legend, in greens."""
    b = [title()]
    x, bw = 24, W - 48
    b.append(f'<clipPath id="pill"><rect x="24" y="54" width="{bw}" height="10" rx="5"/></clipPath><g clip-path="url(#pill)">')
    for i, (n, p) in enumerate(L):
        w = bw * p / 100
        b.append(f'<rect x="{x:.1f}" y="54" width="{w + .5:.1f}" height="10" fill="{SHADES[i]}"/>')
        x += w
    b.append("</g>")
    for i, (n, p) in enumerate(L):
        cx, cy = 24 + (i % 2) * 200, 98 + (i // 2) * 30
        b.append(f'<rect x="{cx}" y="{cy - 9}" width="10" height="10" fill="{SHADES[i]}"/>'
                 f'<text x="{cx + 18}" y="{cy}" font-size="12" fill="{G["mid"]}">{esc(n)} <tspan fill="{G["dim"]}">{p:.2f}%</tspan></text>')
    return b


def donut(L):
    b = [title()]
    cx, cy, r = 110, 118, 52
    a0 = -math.pi / 2
    for i, (n, p) in enumerate(L):
        a1 = a0 + 2 * math.pi * p / 100
        large = 1 if a1 - a0 > math.pi else 0
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1 - .03), cy + r * math.sin(a1 - .03)
        b.append(f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f}" fill="none" stroke="{SHADES[i]}" stroke-width="16"/>')
        a0 = a1
    b.append(f'<text x="{cx}" y="{cy - 2}" font-size="20" font-weight="800" text-anchor="middle" fill="{G["hi"]}">{len(L)}</text>'
             f'<text x="{cx}" y="{cy + 14}" font-size="9" text-anchor="middle" fill="{G["dim"]}">languages</text>')
    for i, (n, p) in enumerate(L):
        y = 70 + i * 21
        b.append(f'<rect x="210" y="{y - 9}" width="10" height="10" fill="{SHADES[i]}"/>'
                 f'<text x="228" y="{y}" font-size="12" fill="{G["mid"]}">{esc(n)}</text>'
                 f'<text x="{W - 24}" y="{y}" font-size="12" text-anchor="end" fill="{G["dim"]}">{p:.2f}%</text>')
    return b


def tree(L):
    b = [title("tree ~/languages")]
    for i, (n, p) in enumerate(L):
        y = 62 + i * 21
        br = "└──" if i == len(L) - 1 else "├──"
        k = max(1, round(p / 100 * 18))
        b.append(f'<text x="24" y="{y}" font-size="12" fill="{G["dim"]}">{br} <tspan fill="{G["txt"]}">{esc(n).lower()}/</tspan></text>'
                 f'<text x="170" y="{y}" font-size="12" fill="{G["mid"]}">{"▪" * k}</text>'
                 f'<text x="{W - 24}" y="{y}" font-size="12" text-anchor="end" fill="{G["dim"]}">{p:.1f}%</text>')
    return b


def columns(L):
    """Vertical columns built from stacked 0/1 glyphs, tallest = most used."""
    b = [title()]
    cw = (W - 48) / len(L)
    base = H - 38
    for i, (n, p) in enumerate(L):
        x = 24 + i * cw + cw / 2
        k = max(1, round(p / L[0][1] * 7))
        for j in range(k):
            a = .35 + .65 * (j + 1) / k
            ch = "1" if (i + j) % 3 else "0"
            col = G["hi"] if j == k - 1 else SHADES[min(i, 5)] if i < 2 else G["txt"]
            b.append(f'<text x="{x:.1f}" y="{base - 6 - j * 13}" font-size="13" font-weight="700" text-anchor="middle" fill="{col}" fill-opacity="{a:.2f}">{ch}</text>')
        b.append(f'<text x="{x:.1f}" y="{base - 12 - k * 13}" font-size="10" text-anchor="middle" fill="{G["dim"]}">{p:.0f}%</text>'
                 f'<text x="{x:.1f}" y="{base + 16}" font-size="11" text-anchor="middle" fill="{G["mid"]}">{esc(n)}</text>')
    b.append(f'<line x1="24" x2="{W - 24}" y1="{base + 2}" y2="{base + 2}" stroke="{G["faint"]}"/>')
    return b


def treemap(L):
    """Squarified-ish slice layout: blocks sized by share."""
    b = [title()]
    x, y, w, h = 24, 50, W - 48, H - 74
    rest = list(L)
    tot = 100.0
    horiz = True
    i = 0
    while rest:
        n, p = rest.pop(0)
        if not rest:
            rw, rh = w, h
        elif horiz:
            rw, rh = w * p / tot, h
        else:
            rw, rh = w, h * p / tot
        b.append(f'<rect x="{x + 1:.1f}" y="{y + 1:.1f}" width="{rw - 2:.1f}" height="{rh - 2:.1f}" fill="{SHADES[i]}" fill-opacity="{.9 - i * .08:.2f}" rx="2"/>')
        dark = i < 3
        # pick a label layout that fits inside the block (1px border + 6px padding)
        c1 = "#001a07" if dark else G["hi"]
        c2 = "#03200c" if dark else G["txt"]
        short = {"TypeScript": "TS", "JavaScript": "JS"}.get(n, n)
        pct = f"{p:.1f}%"
        if rh >= 42:
            fs1, fs2, y1, y2 = (12 if rw > 70 else 10), 10, 18, 32
        else:
            fs1 = fs2 = 9
            pad = (rh - 2 - 20) / 2          # center two 9px lines vertically
            y1, y2 = 1 + pad + 8, 1 + pad + 19
        cw1, cw2 = fs1 * .6, fs2 * .6       # monospace advance ~0.6em
        label = n if len(n) * cw1 <= rw - 14 else short
        if len(label) * cw1 > rw - 14:
            label = label[:max(1, int((rw - 14) / cw1))]
        if rw >= 24 and rh >= 22:
            b.append(f'<text x="{x + 7:.1f}" y="{y + y1:.1f}" font-size="{fs1}" font-weight="700" fill="{c1}">{esc(label)}</text>')
            if len(pct) * cw2 <= rw - 14:
                b.append(f'<text x="{x + 7:.1f}" y="{y + y2:.1f}" font-size="{fs2}" fill="{c2}">{pct}</text>')
        if horiz:
            x += rw; w -= rw
        else:
            y += rh; h -= rh
        tot -= p
        horiz = not horiz
        i += 1
    return b


if __name__ == "__main__":
    L = top6()
    print(L)
    for name, fn in (("a-ascii", ascii_bars), ("b-stacked", stacked), ("c-donut", donut),
                     ("d-tree", tree), ("e-columns", columns), ("f-treemap", treemap)):
        write(f"langs-{name}", svg(W, H, fn(L), "Most used languages", crt=False))

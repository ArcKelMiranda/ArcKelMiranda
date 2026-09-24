"""Aracari Studios — helpers para SVG con texto convertido a trazos.

El texto se dibuja como <path> para que se vea igual en cualquier sistema
(sin depender de fuentes instaladas ni del antialiasing de subpíxel).
"""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = {
    "bold": TTFont(os.path.join(HERE, "fonts", "InstrumentSans-Bold.ttf")),
    "regular": TTFont(os.path.join(HERE, "fonts", "InstrumentSans-Regular.ttf")),
}

BLACK, WHITE, GREY = "#000000", "#FFFFFF", "#BDBDBD"
W = 1280
PAD = 64


def _kern_table(font):
    """Lee pares de kerning (PairPos formato 1 y 2) del GPOS."""
    pairs, classes = {}, []
    if "GPOS" not in font:
        return pairs, classes
    for lookup in font["GPOS"].table.LookupList.Lookup:
        for st in lookup.SubTable:
            if st.LookupType == 9:
                st = st.ExtSubTable
            if getattr(st, "LookupType", None) != 2 and type(st).__name__ != "PairPos":
                continue
            cov = st.Coverage.glyphs
            if st.Format == 1:
                for i, g1 in enumerate(cov):
                    for rec in st.PairSet[i].PairValueRecord:
                        v = rec.Value1.XAdvance if rec.Value1 and hasattr(rec.Value1, "XAdvance") else 0
                        if v:
                            pairs.setdefault((g1, rec.SecondGlyph), v)
            elif st.Format == 2:
                classes.append((set(cov), st.ClassDef1.classDefs, st.ClassDef2.classDefs, st.Class1Record))
    return pairs, classes


_KERN = {k: _kern_table(f) for k, f in FONTS.items()}


def _kern(weight, a, b):
    pairs, classes = _KERN[weight]
    if (a, b) in pairs:
        return pairs[(a, b)]
    for cov, cd1, cd2, recs in classes:
        if a in cov:
            c1, c2 = cd1.get(a, 0), cd2.get(b, 0)
            v = recs[c1].Class2Record[c2].Value1
            x = getattr(v, "XAdvance", 0) if v else 0
            if x:
                return x
    return 0


def text_width(s, size, weight="bold", tracking=0.0):
    font = FONTS[weight]
    cmap, hmtx = font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    scale = size / upm
    w, prev = 0.0, None
    for ch in s:
        g = cmap.get(ord(ch), cmap.get(ord("?")))
        if prev:
            w += _kern(weight, prev, g) * scale
        w += hmtx[g][0] * scale + tracking * size
        prev = g
    return w - (tracking * size if s else 0)


def text(s, x, y, size, weight="bold", fill=WHITE, tracking=0.0, anchor="start"):
    """Devuelve un <path> con el texto s. tracking en em (p.ej. -0.02)."""
    font = FONTS[weight]
    cmap, hmtx, gs = font.getBestCmap(), font["hmtx"], font.getGlyphSet()
    upm = font["head"].unitsPerEm
    scale = size / upm
    width = text_width(s, size, weight, tracking)
    if anchor == "end":
        x -= width
    elif anchor == "middle":
        x -= width / 2
    pen = SVGPathPen(gs, ntos=lambda v: ("%.1f" % v).rstrip("0").rstrip("."))
    cx, prev = x, None
    for ch in s:
        g = cmap.get(ord(ch), cmap.get(ord("?")))
        if prev:
            cx += _kern(weight, prev, g) * scale
        gs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, cx, y)))
        cx += hmtx[g][0] * scale + tracking * size
        prev = g
    d = pen.getCommands()
    return f'<path fill="{fill}" d="{d}"/>' if d else ""


def star(cx, cy, r, fill=WHITE):
    """Glifo ✦ de la marca, dibujado como forma."""
    k = r * 0.22
    d = (f"M{cx} {cy - r} Q{cx + k} {cy - k} {cx + r} {cy} "
         f"Q{cx + k} {cy + k} {cx} {cy + r} Q{cx - k} {cy + k} {cx - r} {cy} "
         f"Q{cx - k} {cy - k} {cx} {cy - r}Z")
    return f'<path fill="{fill}" d="{d}"/>'


def label(s, x, y, size=15, fill=GREY, anchor="start", tracking=0.22):
    """Label de marca: [ TEXTO ] en mayúsculas con tracking amplio."""
    return text(f"[ {s.upper()} ]", x, y, size, "bold", fill, tracking, anchor)


def manifesto(parts, cx, y, size=15, fill=WHITE, tracking=0.24):
    """Frase-manifiesto en caps flanqueada por ✦: ✦ A ✦ B ✦"""
    gap = size * 1.1
    widths = [text_width(p.upper(), size, "bold", tracking) for p in parts]
    total = sum(widths) + gap * 2 * (len(parts) + 1)
    x = cx - total / 2
    out = []
    sy = y - size * 0.36
    for p, w in zip(parts, widths):
        out.append(star(x + gap / 2, sy, size * 0.42, fill)); x += gap * 2
        out.append(text(p.upper(), x - gap / 2, y, size, "bold", fill, tracking)); x += w
    out.append(star(x + gap / 2, sy, size * 0.42, fill))
    return "".join(out)


def rule(y, x1=PAD, x2=W - PAD):
    return f'<rect x="{x1}" y="{y}" width="{x2 - x1}" height="1" fill="{GREY}" fill-opacity=".28"/>'


def panel(h, body, title=None, tag=None, style=""):
    head = ""
    if title:
        head += text(title, PAD, 104, 60, "bold", WHITE, -0.025)
    if tag:
        head += label(tag, W - PAD, 100, 16, GREY, "end")
    if title or tag:
        head += rule(138)
    st = f"<style>{style}</style>" if style else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
            f'viewBox="0 0 {W} {h}">{st}<rect width="{W}" height="{h}" rx="24" fill="{BLACK}"/>'
            f'{head}{body}</svg>')

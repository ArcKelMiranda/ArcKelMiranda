"""Genera los paneles fijos del perfil en assets/.

Edita los textos aquí y corre:  python .github/scripts/build_static.py
(requiere: pip install fonttools)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from aracari_svg import (W, PAD, WHITE, GREY, text, text_width, label,  # noqa: E402
                         manifesto, panel, rule)

OUT = os.path.join(HERE, "..", "..", "assets")
BRAND = os.path.join(HERE, "brand")


def nest(name, prefix, x, y, w, h, recolor=None, extra=""):
    s = open(os.path.join(BRAND, name)).read()
    vb = re.search(r'viewBox="([^"]+)"', s).group(1)
    body = re.sub(r"^.*?<svg[^>]*>", "", s, flags=re.S).rsplit("</svg>", 1)[0]
    for i in set(re.findall(r'id="([^"]+)"', body)):
        body = body.replace(f'id="{i}"', f'id="{prefix}{i}"').replace(f"#{i})", f"#{prefix}{i})").replace(f'"#{i}"', f'"#{prefix}{i}"')
    for a, b in (recolor or {}).items():
        body = body.replace(a, b)
    return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}" fill="none" xmlns:xlink="http://www.w3.org/1999/xlink" {extra}>{body}</svg>'


def wrap(s, size, maxw, weight="regular"):
    lines, cur = [], ""
    for word in s.split():
        t = (cur + " " + word).strip()
        if text_width(t, size, weight) > maxw and cur:
            lines.append(cur)
            cur = word
        else:
            cur = t
    return lines + [cur]


def paragraph(s, x, y, size, maxw, fill=GREY, lh=1.5, weight="regular"):
    out = []
    for i, ln in enumerate(wrap(s, size, maxw, weight)):
        out.append(text(ln, x, y + i * size * lh, size, weight, fill))
    return "".join(out), y + len(wrap(s, size, maxw, weight)) * size * lh


def save(name, svg):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(svg)


# ---------- 00 · HEADER ----------
def header():
    b = [nest("logo-horizontal.svg", "lg", PAD, 46, 260, 260 * 297 / 1522,
              {'fill="#000"': 'fill="#fff"', 'stroke="#000"': 'stroke="#fff"'}),
         label("backend / data / devops", W - PAD, 82, 16, GREY, "end"),
         rule(122),
         text("Kelvin", PAD - 6, 300, 168, "bold", WHITE, -0.035),
         text("Miranda.", PAD - 6, 448, 168, "bold", WHITE, -0.035)]
    p, _ = paragraph("Construyo APIs, pipelines de datos y agentes de IA que llegan a "
                     "producción y se quedan ahí sin dar guerra.", PAD, 518, 28, 700)
    b.append(p)
    b.append(rule(600))
    b.append(label("san salvador, sv", PAD, 646, 15, WHITE))
    b.append(label("working global", W - PAD, 646, 15, WHITE, "end"))
    b.append(f'<g class="sway">{nest("hand-rock.svg", "hr", 905, 140, 290, 290)}</g>')
    b.append(f'<g transform="rotate(-7 1045 500)">'
             f'{nest("car-plate.svg", "cp", 915, 440, 260, 260 * 383 / 795)}</g>')
    style = (".sway{transform-origin:1050px 285px;animation:s 7s ease-in-out infinite}"
             "@keyframes s{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(5deg)}}"
             "@media (prefers-reduced-motion:reduce){.sway{animation:none}}")
    save("header.svg", panel(690, "".join(b), style=style))


# ---------- 01 · SOBRE MÍ ----------
def about():
    b = []
    p1, y = paragraph("Developer en Aracari Studios. Trabajo desde El Salvador en backend, "
                      "ingeniería de datos y la infraestructura que los mantiene vivos.",
                      PAD, 206, 28, 740, WHITE)
    p2, y = paragraph("Ahora construyo el ecosistema YHAT: un SDK de ETL, un servidor MCP y una "
                      "plataforma de conocimiento con agentes que capturan lo que el equipo sabe. "
                      "En mis ratos libres escribo un CRM en Rust para pelearme con el borrow checker.",
                      PAD, y + 22, 24, 740, GREY)
    b += [p1, p2]
    b.append(nest("cookie-cutter.svg", "cc", 900, 170, 300, 300))
    top = max(y + 30, 500)
    b.append(rule(top))
    rules = [("main", "protegida, siempre"),
             ("flujo", "rama → PR → review → CI verde → merge"),
             ("push --force", "no.")]
    for i, (k, v) in enumerate(rules):
        yy = top + 62 + i * 58
        b.append(label(k, PAD, yy, 15, GREY))
        b.append(text(v, 330, yy + 2, 26, "bold", WHITE, -0.01))
    save("about.svg", panel(int(top + 62 + 3 * 58 + 10), "".join(b), "Sobre mí", "01 / sobre mí"))


# ---------- 02 · STACK ----------
def stack():
    groups = [("lenguajes", ["Python", "TypeScript", "Go", "Rust", "SQL"]),
              ("backend + frontend", ["FastAPI", "React", "Astro", "Vite", "Node.js"]),
              ("datos", ["PostgreSQL", "SQL Server", "Airflow", "Jupyter"]),
              ("infra + IA", ["Docker", "Linux", "Tailscale", "GitHub Actions", "MCP"])]
    colw = (W - 2 * PAD) / 4
    b = []
    for gi, (g, items) in enumerate(groups):
        x = PAD + gi * colw
        b.append(label(g, x, 196, 14, GREY))
        for ii, it in enumerate(items):
            b.append(text(it, x, 256 + ii * 58, 32, "bold", WHITE, -0.015))
    save("stack.svg", panel(256 + 4 * 58 + 56, "".join(b), "Con qué construyo", "02 / stack"))


# ---------- 03 · PROYECTOS ----------
def projects():
    projs = [("yhat-agent", "CLI en Go para capturar conocimiento", "Go", "work"),
             ("YHAT SDK", "ETL con pipelines orquestados", "Python + Airflow", "work"),
             ("YHAT MCP Server", "Conecta LLMs con datos vía MCP", "TypeScript", "work"),
             ("YHAT Knowledge", "Plataforma de conocimiento", "FastAPI + Vite", "work"),
             ("Stacks Dashboard", "Monitorea mis stacks de Docker", "Python + Docker", "work"),
             ("Finanza App", "Finanzas personales, sin Excel", "FastAPI + React", "personal"),
             ("Evolution Beauty", "Sitio con render en servidor", "Astro SSR", "personal"),
             ("Prototype CRM", "Un CRM en Rust, porque sí", "Rust + PostgreSQL", "personal")]
    b, rowh, top = [], 86, 150
    for i, (n, d, s, t) in enumerate(projs):
        y = top + i * rowh
        if i:
            b.append(rule(y))
        b.append(text(f"{i + 1:02d}.", PAD, y + 54, 18, "bold", GREY, 0.08))
        b.append(text(n, PAD + 58, y + 56, 32, "bold", WHITE, -0.02))
        b.append(text(d, 520, y + 54, 22, "regular", GREY))
        b.append(label(t, W - PAD, y + 38, 13, WHITE, "end"))
        b.append(text(s, W - PAD, y + 66, 18, "regular", GREY, anchor="end"))
    save("projects.svg", panel(top + 8 * rowh + 30, "".join(b), "En qué ando", "03 / proyectos"))


# ---------- FOOTER ----------
def footer():
    b = [text("¿Construimos algo?", W / 2, 150, 76, "bold", WHITE, -0.03, "middle"),
         text("Abre un issue, manda un PR o escríbeme por Aracari Studios.",
              W / 2, 204, 26, "regular", GREY, anchor="middle"),
         manifesto(["no fluff", "no excuses"], W / 2, 282, 16),
         nest("wordmark-light.svg", "wm", W / 2 - 90, 312, 180, 180 * 291 / 838)]
    save("footer.svg", panel(410, "".join(b)))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    header(); about(); stack(); projects(); footer()
    print("paneles listos")

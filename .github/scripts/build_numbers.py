"""Genera assets/numbers.svg con datos reales de GitHub (GraphQL).

Uso en Actions:  GITHUB_TOKEN=... USER=ArcKelMiranda python build_numbers.py
Uso local sin red: python build_numbers.py --demo 122 1 2
"""
import datetime as dt
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aracari_svg import W, PAD, WHITE, GREY, text, text_width, label, panel, rule  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "numbers.svg")
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
LEVELS = ["#161616", "#3D3D3D", "#6E6E6E", "#BDBDBD", "#FFFFFF"]

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{ totalContributions
        weeks{ contributionDays{ date contributionCount } } }
    }
    repositories(ownerAffiliations:OWNER, privacy:PUBLIC, first:100, isFork:false){
      totalCount nodes{ stargazerCount } }
  }
}"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "aracari-profile"})
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]


def streaks(days):
    counts = [d["contributionCount"] for d in days]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    cur, i = 0, len(counts) - 1
    if i >= 0 and counts[i] == 0:  # hoy todavía sin contribuir: no rompe la racha
        i -= 1
    while i >= 0 and counts[i]:
        cur += 1
        i -= 1
    return cur, longest


def level(c, mx):
    if c == 0 or mx == 0:
        return 0
    return min(4, 1 + int(3.999 * c / mx))


def render(total, cur, longest, repos, stars, weeks):
    body = []
    # Cifras grandes
    stats = [(f"{total:,}".replace(",", "."), "contribuciones", "último año"),
             (str(cur), "racha actual", "día seguido" if cur == 1 else "días seguidos"),
             (str(longest), "racha más larga", "día seguido" if longest == 1 else "días seguidos"),
             (str(repos), "repos públicos", f"{stars} estrellas" if stars != "—" else "—")]
    colw = (W - 2 * PAD) / 4
    for i, (big, l1, l2) in enumerate(stats):
        x = PAD + i * colw
        body.append(text(big, x - 3, 266, 86, "bold", WHITE, -0.03))
        body.append(text(l1, x, 312, 22, "regular", WHITE))
        body.append(text(l2, x, 342, 22, "regular", GREY))
    body.append(rule(386))

    # Mapa de contribuciones (53 semanas x 7 días)
    top = 452
    n = len(weeks) or 53
    step = (W - 2 * PAD) / n
    size = step - 4
    mx = max([d["contributionCount"] for w in weeks for d in w["contributionDays"]] or [0])
    last_month = None
    for wi, w in enumerate(weeks):
        x = PAD + wi * step
        for d in w["contributionDays"]:
            day = dt.date.fromisoformat(d["date"])
            y = top + ((day.weekday() + 1) % 7) * step
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{size:.1f}" height="{size:.1f}" '
                        f'rx="3" fill="{LEVELS[level(d["contributionCount"], mx)]}"/>')
        first = dt.date.fromisoformat(w["contributionDays"][0]["date"])
        if first.month != last_month and wi < n - 2:
            if last_month is not None or first.day <= 7:
                body.append(text(MESES[first.month - 1], x, top - 16, 16, "regular", GREY))
            last_month = first.month
    # Leyenda
    ly = top + 7 * step + 40
    end = W - PAD - text_width("más", 16, "regular") - 12
    start = end - 5 * 26 + 8
    body.append(text("menos", start - 12, ly + 15, 16, "regular", GREY, anchor="end"))
    for i, c in enumerate(LEVELS):
        body.append(f'<rect x="{start + i * 26}" y="{ly}" width="18" height="18" rx="3" fill="{c}"/>')
    body.append(text("más", W - PAD, ly + 15, 16, "regular", GREY, anchor="end"))
    stamp = dt.date.today().strftime("%d/%m/%Y")
    body.append(label(f"actualizado {stamp}", PAD, ly + 15, 14, GREY))
    h = int(ly + 70)
    return panel(h, "".join(body), "Los números", "04 / números")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        total, cur, longest = map(int, sys.argv[2:5])
        today = dt.date.today()
        start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
        weeks = [{"contributionDays": [{"date": (start + dt.timedelta(days=w * 7 + d)).isoformat(),
                                        "contributionCount": 0} for d in range(7)
                                       if start + dt.timedelta(days=w * 7 + d) <= today]}
                 for w in range(53)]
        svg = render(total, cur, longest, "—", "—", weeks)
    else:
        u = fetch(os.environ["USER_LOGIN"], os.environ["GITHUB_TOKEN"])
        cal = u["contributionsCollection"]["contributionCalendar"]
        days = [d for w in cal["weeks"] for d in w["contributionDays"]]
        cur, longest = streaks(days)
        stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
        svg = render(cal["totalContributions"], cur, longest,
                     u["repositories"]["totalCount"], stars, cal["weeks"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(svg)
    print("numbers.svg listo")


if __name__ == "__main__":
    main()

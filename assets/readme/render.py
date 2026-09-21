#!/usr/bin/env python3
"""Render the README diagrams (standard library only).

    python3 -B assets/readme/render.py

Writes fabius-loop.svg, fabius-system.svg, fabius-ladder.svg and cta-install.svg (README) and
benchmark-panel-a.svg (BENCHMARKS.md) beside this file. The diagram labels come from the tables below,
which mirror skills/fabius/SKILL.md (the loop, the routing table) and skills/fabius/references/
routing-policy.md (rule R2): they show how Fabius works and are not measurements. The one chart of
measured data reads every number from the committed receipts (evals/results.v5.json, checked against
evals/results.benchmark.json) and fails if the two disagree. All of this is separate from
assets/charts/, whose outputs are whitepaper sources.

The cards are self-contained dark surfaces so they read on GitHub's light and dark themes. Text uses
system font stacks (an SVG shown through <img> cannot load a web font) and is sized on an 840-unit
canvas so the main labels stay legible when GitHub scales the image to a 324px phone column.
"""
from math import cos, pi, sin
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent
W = 840

# -- tokens ------------------------------------------------------------------------------------
GROUND = "#0e1511"        # matches the ground of assets/fabius-contour.webp
EDGE = "#76b900"          # card edge, drawn at low opacity
ACCENT = "#76b900"
ACCENT_LITE = "#9ade2b"
ACCENT_DEEP = "#5e9400"
NODE = "#141d17"
NODE_EDGE = "#ffffff"     # drawn at low opacity
TEXT = "#ffffff"
BODY = "#e4eadf"
MUTED = "#9aa79b"
ON_ACCENT = "#000000"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

# -- content -----------------------------------------------------------------------------------
LOOP = [  # skills/fabius/SKILL.md, "The loop"
    ("1", "Sense", ["read the project", "record and the", "code first"], "archivum"),
    ("2", "Classify", ["name what it needs;", "ask only what", "changes the outcome"], "disciplina"),
    ("3", "Route", ["pick the skills, the", "machinery rung,", "the model tier"], "disciplina"),
    ("4", "Strike", ["make the smallest", "correct change"], "parcus"),
    ("5", "Prove", ["run it and show", "the evidence, never", "“should work”"], "disciplina"),
    ("6", "Compound", ["file the verified", "lesson, with your", "permission"], "archivum"),
]

SPECIALISTS = [  # order of the routing table in skills/fabius/SKILL.md
    ("disciplina", "engineering process"),
    ("decor", "design + charts"),
    ("cohors", "agent engineering"),
    ("archivum", "project memory"),
    ("mercatus", "go-to-market"),
    ("praesidium", "defensive security"),
    ("ludus", "small-game craft"),
    ("catena", "on-chain + sealing"),
    ("machina", "automation"),
    ("scientia", "science method"),
    ("doctrina", "AI/ML engineering"),
    ("fortuna", "markets, never advice"),
    ("concilium", "multi-model council"),
]

LADDER = [  # routing-policy.md, rule R2 — plain-language rung names, contract names in mono
    ("1", "answer inline", "parcus inline"),
    ("2", "one tool call", "one tool call"),
    ("3", "retrieval", "archivum retrieval"),
    ("4", "a written plan", "disciplina plan"),
    ("5", "a single subagent", "single subagent"),
    ("6", "a swarm", "cohors swarm"),
]
LADDER_HELD = 2  # the worked example: rung 1 was not enough, rung 2 held


# -- svg helpers -------------------------------------------------------------------------------
def text(x, y, s, size, fill=BODY, family=SANS, weight=400, anchor="start", spacing=None, opacity=None):
    extra = ""
    if spacing is not None:
        extra += f' letter-spacing="{spacing}"'
    if opacity is not None:
        extra += f' opacity="{opacity}"'
    return (f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{size:g}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{escape(s)}</text>')


def rect(x, y, w, h, rx, fill="none", stroke=None, sw=1.5, so=None, dash=None, fo=None):
    a = f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}" fill="{fill}"'
    if fo is not None:
        a += f' fill-opacity="{fo}"'
    if stroke:
        a += f' stroke="{stroke}" stroke-width="{sw:g}"'
        if so is not None:
            a += f' stroke-opacity="{so}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
    return a + "/>"


def line(x1, y1, x2, y2, stroke=ACCENT, sw=2, so=None, marker=True):
    a = f'<path d="M{x1:g} {y1:g} L{x2:g} {y2:g}" fill="none" stroke="{stroke}" stroke-width="{sw:g}" stroke-linecap="round"'
    if so is not None:
        a += f' stroke-opacity="{so}"'
    if marker:
        a += ' marker-end="url(#arrow)"'
    return a + "/>"


def contours(cx, cy, radius, rings, seed):
    """A quiet topographic motif behind the content: one perturbed ring, repeated at growing radii."""
    a, b, p, q = 0.11 + 0.02 * seed, 0.06, 0.7 * seed, 1.9 * seed
    paths = []
    for k in range(rings):
        r = radius * (0.22 + 0.78 * (k + 1) / rings)
        pts = []
        for i in range(73):
            t = 2 * pi * i / 72
            rr = r * (1 + a * sin(3 * t + p) + b * sin(5 * t + q))
            pts.append(f"{cx + rr * cos(t) * 1.35:.1f} {cy + rr * sin(t):.1f}")
        paths.append(f'<path d="M{" L".join(pts)} Z"/>')
    return ('<g fill="none" stroke="%s" stroke-width="1" stroke-opacity=".13" clip-path="url(#card)">%s</g>'
            % (ACCENT, "".join(paths)))


def card(height, title, desc, body, motif):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height:g}" width="{W}" height="{height:g}" '
        f'role="img" aria-labelledby="t d">\n<title id="t">{escape(title)}</title>\n<desc id="d">{escape(desc)}</desc>\n'
        f'<defs><clipPath id="card"><rect x="1" y="1" width="{W - 2}" height="{height - 2:g}" rx="16"/></clipPath>'
        f'<marker id="arrow" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M1 1 L9 5 L1 9" fill="none" stroke="{ACCENT}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</marker></defs>\n'
        + rect(1, 1, W - 2, height - 2, 16, fill=GROUND, stroke=EDGE, sw=1.5, so=".32") + "\n"
        + motif + "\n" + "\n".join(body) + "\n</svg>\n"
    )


# -- 1 · the loop ------------------------------------------------------------------------------
def loop_svg():
    cw, ch, gap, mx = 252, 176, 18, 24
    top = 78
    row2 = top + ch + 46
    height = row2 + ch + 74
    b = [text(mx, 46, "SCOUT WIDE · STRIKE NARROW", 19, ACCENT_LITE, MONO, 600, spacing="2.5"),
         text(W - mx, 46, "tag = the skill that owns the step", 18.5, MUTED, SANS, 400, "end"),
         text(mx, height - 28, "how every task runs", 19, MUTED, SANS, 400),
         text(W - mx, height - 28, "the loop closes: the next task starts ahead", 19, MUTED, SANS, 400, "end")]
    # top row runs left to right (1-3), bottom row right to left (4-6): the flow is a closed loop
    slots = [(0, top), (1, top), (2, top), (2, row2), (1, row2), (0, row2)]
    for (num, name, lines, owner), (col, y) in zip(LOOP, slots):
        x = mx + col * (cw + gap)
        b.append(rect(x, y, cw, ch, 14, fill=NODE, stroke=NODE_EDGE, sw=1.2, so=".13"))
        b.append(text(x + 20, y + 40, num, 22, ACCENT, MONO, 700))
        b.append(text(x + 46, y + 42, name, 30, TEXT, SANS, 700))
        for i, ln in enumerate(lines):
            b.append(text(x + 20, y + 78 + i * 27, ln, 20.5, BODY))
        b.append(text(x + cw - 18, y + ch - 18, owner, 17.5, ACCENT_LITE, MONO, 500, "end", opacity=".9"))
    ymid1, ymid2 = top + ch / 2, row2 + ch / 2
    for col in (0, 1):
        x = mx + col * (cw + gap) + cw
        b.append(line(x + 2, ymid1, x + gap - 3, ymid1))
        b.append(line(x + gap - 2, ymid2, x + 3, ymid2))
    xr = mx + 2 * (cw + gap) + cw / 2
    xl = mx + cw / 2
    b.append(line(xr, top + ch + 3, xr, row2 - 5))
    b.append(line(xl, row2 - 3, xl, top + ch + 5))
    return card(height, "How every Fabius task runs: a six-step loop",
                "Sense, read the project record and the code first. Classify, name what the task needs and ask only what changes "
                "the outcome. Route, pick the skills, the machinery rung and the model tier. Strike, make the smallest "
                "correct change. Prove, run it and show the evidence. Compound, file the verified lesson with your "
                "permission. Scout wide, strike narrow; then the loop closes and the next task starts ahead.",
                b, contours(640, 120, 420, 9, 1))


# -- 2 · the system ----------------------------------------------------------------------------
def system_svg():
    mx, cols, gap = 24, 3, 14
    cx = W / 2
    y = 28
    b = []
    b.append(rect(cx - 150, y, 300, 50, 25, fill=NODE, stroke=NODE_EDGE, sw=1.2, so=".18"))
    b.append(text(cx, y + 33, "your request", 22, TEXT, SANS, 600, "middle"))
    b.append(line(cx, y + 53, cx, y + 80))
    y += 86
    b.append(rect(cx - 300, y, 600, 106, 16, fill="#131c0c", stroke=ACCENT_LITE, sw=1.8, so=".7"))
    b.append(text(cx, y + 42, "fabius", 31, ACCENT_LITE, MONO, 700, "middle"))
    b.append(text(cx, y + 70, "the router", 20, TEXT, SANS, 600, "middle"))
    b.append(text(cx, y + 94, "picks the skills · the machinery · the model tier", 19.5, BODY, SANS, 400, "middle"))
    b.append(line(cx, y + 109, cx, y + 140))
    y += 146
    rows = (len(SPECIALISTS) + cols - 1) // cols
    nh = 72
    inner = W - 2 * mx - 2 * 18
    nw = (inner - (cols - 1) * gap) / cols
    box_h = 54 + rows * nh + (rows - 1) * gap + 20
    b.append(rect(mx, y, W - 2 * mx, box_h, 16, fill="#0b110d", stroke=ACCENT, sw=1.2, so=".3", dash="5 5"))
    b.append(text(mx + 20, y + 34, "THIRTEEN SPECIALISTS", 18, ACCENT_LITE, MONO, 600, spacing="2.5"))
    b.append(text(W - mx - 20, y + 34, "loaded only when the task needs them", 18.5, MUTED, SANS, 400, "end"))
    gy = y + 54
    for i, (name, role) in enumerate(SPECIALISTS):
        r, c = divmod(i, cols)
        in_row = min(cols, len(SPECIALISTS) - r * cols)
        row_w = in_row * nw + (in_row - 1) * gap
        x0 = mx + 18 + (inner - row_w) / 2
        x = x0 + c * (nw + gap)
        yy = gy + r * (nh + gap)
        b.append(rect(x, yy, nw, nh, 12, fill=NODE, stroke=NODE_EDGE, sw=1.2, so=".13"))
        b.append(text(x + 18, yy + 31, name, 24, TEXT, MONO, 700))
        b.append(text(x + 18, yy + 57, role, 19.5, BODY))
    y += box_h + 16
    b.append(rect(mx, y, W - 2 * mx, 90, 14, fill=ACCENT))
    b.append(text(mx + 22, y + 38, "fabius-parcus", 26, ON_ACCENT, MONO, 700))
    b.append(text(W - mx - 22, y + 37, "the lean core · always on, underneath", 19.5, ON_ACCENT, SANS, 600, "end"))
    b.append(text(mx + 22, y + 70, "say less · build less · change less · assume less", 20, ON_ACCENT, SANS, 500))
    b.append(line(cx, y + 93, cx, y + 120))
    y += 126
    b.append(rect(cx - 250, y, 500, 50, 25, fill=NODE, stroke=NODE_EDGE, sw=1.2, so=".18"))
    b.append(text(cx, y + 33, "the smallest correct result, with its evidence", 20.5, TEXT, SANS, 600, "middle"))
    y += 50 + 44
    b.append(text(cx, y, "fifteen skills = 1 router + 1 always-on core + 13 specialists", 18, MUTED, MONO, 400, "middle"))
    height = y + 28
    names = ", ".join(f"{n} ({r})" for n, r in SPECIALISTS)
    return card(height, "The Fabius system: one router, thirteen specialists, one always-on lean core",
                "Your request goes to the fabius router, which picks the skills, the machinery and the model tier. "
                f"Thirteen specialists are loaded only when the task needs them: {names}. The fabius-parcus lean core "
                "is always on underneath: say less, build less, change less, assume less. The output is the smallest "
                "correct result, with its evidence. Fifteen skills in total.",
                b, contours(180, 330, 520, 11, 2))


# -- 3 · the ladder ----------------------------------------------------------------------------
def ladder_svg():
    mx, bh, gap = 24, 54, 10
    top = 96
    b = [text(mx, 44, "THE MACHINERY LADDER", 19, ACCENT_LITE, MONO, 600, spacing="3"),
         text(mx, 74, "One rung at a time. Fabius stops at the first rung that holds.", 22, TEXT, SANS, 600)]
    n = len(LADDER)
    full = W - 2 * mx
    for i, (num, label, contract) in enumerate(LADDER):
        idx = i + 1
        y = top + i * (bh + gap)
        w = full * (0.55 + 0.45 * i / (n - 1))
        held, tried = idx == LADDER_HELD, idx < LADDER_HELD
        if held:
            b.append(rect(mx, y, w, bh, 10, fill=ACCENT))
            ink, sub = ON_ACCENT, ON_ACCENT
        elif tried:
            b.append(rect(mx, y, w, bh, 10, fill=ACCENT_DEEP, fo=".55", stroke=ACCENT, sw=1.2, so=".5"))
            ink, sub = TEXT, BODY
        else:
            b.append(rect(mx, y, w, bh, 10, fill="none", stroke=NODE_EDGE, sw=1.2, so=".22", dash="6 5"))
            ink, sub = BODY, MUTED
        b.append(text(mx + 18, y + 35, num, 21, ink if held else (ACCENT_LITE if tried else MUTED), MONO, 700))
        b.append(text(mx + 46, y + 35, label, 23, ink, SANS, 600))
        state = "held → stop" if held else ("not enough" if tried else "never started")
        b.append(text(mx + w - 18, y + 35, state, 18.5, sub, MONO, 600 if held else 400, "end"))
    y = top + n * (bh + gap) + 26
    b.append(text(mx, y, "Example: a task that one tool call settles. Rungs 3–6 are never started.", 19.5, BODY))
    b.append(text(mx, y + 32, "Never start the next rung until this one is shown insufficient on this task.", 19.5, MUTED))
    height = y + 32 + 34
    return card(height, "The machinery ladder: Fabius adds capability one rung at a time and stops at the first that holds",
                "Six rungs: answer inline, one tool call, retrieval, a written plan, a single subagent, a swarm. "
                "In the example, answering inline was tried and was not enough, one tool call held, so Fabius stopped; "
                "retrieval, a plan, a subagent and a swarm were never started. The rule: never start the next rung until this one "
                "is shown insufficient on this task. This is a diagram of the rule, not a measurement.",
                b, contours(700, 360, 380, 8, 3))


# -- 4 · the install button --------------------------------------------------------------------
def cta_svg():
    w, h = 350, 52
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="Install Fabius in your agent app"><title>Install Fabius in your agent app</title>'
            + rect(0, 0, w, h, 6, fill=ACCENT)
            + text(w / 2, 33, "Install in your agent app  →", 20, ON_ACCENT, SANS, 700, "middle")
            + "</svg>\n")


# -- 5 · benchmark Panel A (BENCHMARKS.md) ------------------------------------------------------
# The only chart of measured data. Every number is read from the committed receipts at render time:
# evals/results.v5.json (per-arm score and answer length) and evals/results.benchmark.json (the
# published aggregate, which must agree). Nothing below is typed by hand.
REPO = OUT.parent.parent
PANEL_A_ORDER = [("fable", "Fable 5"), ("sonnet", "Sonnet 5"), ("opus", "Opus 4.8"), ("haiku", "Haiku 4.5")]
ARMS = [  # (receipt key, legend label, mark)
    ("baseline", "the task alone", "dot-grey"),
    ("terse", "+ a “be concise” line", "ring"),
    ("fabius", "+ the Fabius rules", "dot-green"),
]
GREY = "#8d9a8f"


def panel_a_data():
    import json
    import re
    raw = json.loads((REPO / "evals/results.v5.json").read_text(encoding="utf-8"))
    pub = json.loads((REPO / "evals/results.benchmark.json").read_text(encoding="utf-8"))["panelA_quality_newest_claude"]
    rows = []
    for key, name in PANEL_A_ORDER:
        arm = {a: raw["byModelArm"][f"{key}/{a}"] for a, _, _ in ARMS}
        pubm = pub["byModel"][key]
        for a, _, _ in ARMS:  # the chart must show exactly what the published table shows
            assert abs(arm[a]["total"] - pubm[a]) < 1e-9, (key, a, arm[a]["total"], pubm[a])
        assert arm["baseline"]["chars"] == pubm["baseline_chars"] and arm["fabius"]["chars"] == pubm["fabius_chars"], key
        rows.append({"key": key, "name": name,
                     "score": {a: arm[a]["total"] for a, _, _ in ARMS},
                     "chars": {a: arm[a]["chars"] for a, _, _ in ARMS},
                     "n": arm["fabius"]["n"]})
    date = re.search(r"\d{4}-\d{2}-\d{2}", pub["method"]).group(0)
    gap = pub["judgeAgreement"]["mean_abs_total_diff"]
    return rows, date, gap


def mark(kind, x, y, r=7.5):
    if kind == "ring":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:g}" fill="{GROUND}" stroke="{BODY}" stroke-width="2.4"/>'
    fill = ACCENT if kind == "dot-green" else GREY
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:g}" fill="{fill}" stroke="{GROUND}" stroke-width="2"/>'


def benchmark_svg():
    rows, date, gap = panel_a_data()
    mx, x0, x1 = 24, 214, 704
    rh, dodge = 72, 15
    b = []
    better = [r for r in rows if r["score"]["fabius"] > r["score"]["baseline"]]
    lower = [r for r in rows if r["score"]["fabius"] < r["score"]["baseline"]]
    cuts = [100 * (1 - r["chars"]["fabius"] / r["chars"]["baseline"]) for r in rows]
    terse_shorter = sum(r["chars"]["terse"] < r["chars"]["fabius"] for r in rows)
    words = {1: "one", 2: "two", 3: "three", 4: "four"}
    b.append(text(mx, 44, f"PANEL A · RUN OF {date} · FOUR CLAUDE TIERS", 18, ACCENT_LITE, MONO, 600, spacing="2"))
    b.append(text(mx, 84, f"Shorter answers on all {words[len(rows)]} tiers, a higher score on {words[len(better)]}", 25.5, TEXT, SANS, 700))
    b.append(text(mx, 116, f"Same model, same {rows[0]['n']} tasks, three ways. Two judges scored every answer blind.", 19.5, BODY))
    lx = mx
    for _, label, kind in ARMS:
        b.append(mark(kind, lx + 8, 154))
        b.append(text(lx + 24, 161, label, 19.5, BODY))
        lx += 24 + len(label) * 9.6 + 34

    def panel(top, title, note, lo, hi, ticks, fmt, value, right):
        out = [text(mx, top, title, 21, TEXT, SANS, 600), text(W - mx, top, note, 17.5, MUTED, SANS, 400, "end")]
        gy0, gy1 = top + 18, top + 18 + len(rows) * rh
        sx = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
        for t in ticks:
            out.append(f'<path d="M{sx(t):.1f} {gy0} V{gy1}" stroke="{NODE_EDGE}" stroke-opacity=".12" stroke-width="1"/>')
            out.append(text(sx(t), gy1 + 24, fmt(t), 18, MUTED, MONO, 400, "middle"))
        for i, r in enumerate(rows):
            cy = gy0 + i * rh + rh / 2
            out.append(rect(mx - 6, gy0 + i * rh + 4, W - 2 * mx + 12, rh - 8, 10, fill=NODE, fo=".55"))
            out.append(text(mx + 8, cy + 7, r["name"], 21, TEXT, SANS, 600))
            for j, (a, _, kind) in enumerate(ARMS):
                out.append(mark(kind, sx(value(r, a)), cy + (j - 1) * dodge))
            out.append(text(W - mx - 8, cy + 7, right(r), 20, BODY, MONO, 600, "end"))
        return out, gy1 + 24

    top = 222
    p1, end = panel(top, "Score out of 15", "Fabius vs the task alone", 11, 15, [11, 12, 13, 14, 15],
                    lambda t: f"{t}", lambda r, a: r["score"][a],
                    lambda r: f'{r["score"]["fabius"] - r["score"]["baseline"]:+.2f}'.replace("-", "−"))
    b += p1
    top = end + 62
    p2, end = panel(top, "Average answer length, characters", "Fabius vs the task alone", 0, 4500,
                    [0, 1000, 2000, 3000, 4000], lambda t: "0" if t == 0 else f"{t // 1000}k",
                    lambda r, a: r["chars"][a],
                    lambda r: f'−{100 * (1 - r["chars"]["fabius"] / r["chars"]["baseline"]):.1f}%')
    b += p2
    y = end + 44
    import datetime
    month = datetime.date.fromisoformat(date).strftime("%B %Y")
    shorter = "every tier" if terse_shorter == len(rows) else f"{words[terse_shorter]} of {words[len(rows)]} tiers"
    notes = [
        f"The plain “be concise” line wrote shorter still, on {shorter}.",
        f"{', '.join(r['name'] for r in lower)} scored lower with Fabius."
        if lower else "No tier scored lower with Fabius.",
        f"The two judges differ by {gap:g} of 15 on average: read the score gaps as small.",
        f"Measured in {month} before Fabius 3.x existed. Data: evals/results.v5.json.",
    ]
    for i, n in enumerate(notes):
        b.append(text(mx, y + i * 30, n, 19, BODY if i < 2 else MUTED))
    height = y + (len(notes) - 1) * 30 + 34
    desc = (f"Panel A, run of {date}: the same four Claude models answered the same {rows[0]['n']} tasks three ways, "
            "the task alone, the task plus a be-concise line, and the task plus the Fabius rules, scored blind out of 15 "
            "by two judges. " + " ".join(
                f"{r['name']}: score {r['score']['baseline']:.2f}, {r['score']['terse']:.2f}, {r['score']['fabius']:.2f}; "
                f"average length {r['chars']['baseline']}, {r['chars']['terse']}, {r['chars']['fabius']} characters."
                for r in rows)
            + f" Fabius answers were {min(cuts):.1f} to {max(cuts):.1f} percent shorter than the task alone on every tier; "
            f"the be-concise line was shorter still on {shorter}. " + notes[1] + " " + notes[2] + " " + notes[3])
    return card(height, "Benchmark Panel A: score and answer length for four Claude tiers, three ways", desc, b,
                contours(720, 260, 360, 7, 4))


def main():
    for name, svg in (("fabius-loop.svg", loop_svg()), ("fabius-system.svg", system_svg()),
                      ("fabius-ladder.svg", ladder_svg()), ("cta-install.svg", cta_svg()),
                      ("benchmark-panel-a.svg", benchmark_svg())):
        (OUT / name).write_text(svg, encoding="utf-8")
        print("wrote", name, len(svg), "bytes")


if __name__ == "__main__":
    main()

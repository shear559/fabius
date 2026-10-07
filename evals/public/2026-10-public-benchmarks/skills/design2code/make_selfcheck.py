#!/usr/bin/env python3
"""Self-check of score.py -> selfcheck.json (+ selfcheck/<set>.out.jsonl as evidence).

Response sets (one response per item, all 80 items):
  gold            the reference HTML itself, in a ```html block after a one-line preamble
  gold_rerun      the same again with the final score.py (determinism + `passed` end to end)
  wrong_unrelated the reference HTML of ANOTHER sampled page (item k gets item k+1's)
  wrong_blank     a valid but empty HTML page
  wrong_prose     a prose refusal with no HTML (official pipeline wraps it in <p>)
  partial_text    the right visible text, no styling or layout (a curve point, not a check)
  gpt4v_official  the OFFICIAL released GPT-4V direct-prompting predictions for these
                  items, compared with the OFFICIAL released per-item scores
Also: extraction unit tests and render fidelity (re-rendered reference vs published PNG).

usage: python make_selfcheck.py [--sets a,b,...] [--jobs N] [--force]
"""
import argparse
import json
import re
import shutil
import statistics as st
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SC = HERE / "selfcheck"
sys.path.insert(0, str(HERE))
import score  # noqa: E402

ALL_SETS = ["gold", "wrong_unrelated", "wrong_blank", "wrong_prose", "partial_text", "gpt4v_official", "gold_rerun"]
BLANK = "<!DOCTYPE html>\n<html><head><title>Page</title></head><body></body></html>"
PROSE = "I'm sorry, but I can't reproduce this webpage."
SUBS = ("block_match", "text", "position", "color", "clip")


def visible_text(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["style", "script", "head", "title", "noscript"]):
        t.decompose()
    lines = [ln.strip() for ln in soup.get_text("\n").split("\n") if ln.strip()]
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return "<!DOCTYPE html>\n<html><body>\n" + "\n".join(f"<p>{esc(l)}</p>" for l in lines) + "\n</body></html>"


def make_set(name, items):
    if name == "gpt4v_official":  # stored copy of the released predictions (see official_scores.json)
        return [json.loads(l) for l in open(SC / "gpt4v_direct.responses.jsonl")]
    refs = [(HERE / it["gold"]["ref_html"]).read_text(encoding="utf-8", errors="replace") for it in items]
    fence = lambda h: f"Here is the HTML:\n\n```html\n{h}\n```\n"
    pick = {"gold": lambda k: fence(refs[k]), "gold_rerun": lambda k: fence(refs[k]),
            "wrong_unrelated": lambda k: fence(refs[(k + 1) % len(items)]),
            "wrong_blank": lambda k: fence(BLANK), "wrong_prose": lambda k: PROSE,
            "partial_text": lambda k: fence(visible_text(refs[k]))}[name]
    return [{"item": it["item"], "response": pick(k)} for k, it in enumerate(items)]


def extraction_tests():
    doc = "<!DOCTYPE html>\n<html><body><p>Hi</p></body></html>"
    cases = [
        ("fenced only", f"```html\n{doc}\n```", doc),
        ("prose around fence", f"Sure.\n\n```html\n{doc}\n```\n\nNotes: done.", doc),
        ("lowercase doctype + prose", "Here:\n```html\n<!doctype html>\n<html><body>x</body></html>\n```\nBye",
         "<!doctype html>\n<html><body>x</body></html>"),
        ("unterminated fence", f"```html\n{doc[:-7]}", doc[:-7]),
        ("raw html with prose (official cleanup)", f"Sure!\n{doc}\nDone.", doc),
        ("css block + html block -> html block", f"```css\np{{}}\n```\n```html\n{doc}\n```", doc),
        ("prose only kept as text (official)", "No code here.", "No code here."),
        ("empty", "", ""),
    ]
    res = [{"case": c, "ok": score.extract_html(r) == want} for c, r, want in cases]
    return {"passed": sum(r["ok"] for r in res), "total": len(res), "cases": res}


def run_set(name, items, jobs, force):
    out = SC / f"{name}.out.jsonl"
    if out.exists() and not force:
        return
    resp = SC / f"{name}.responses.jsonl"
    stored = name == "gpt4v_official"
    if not stored:
        with open(resp, "w") as f:
            for r in make_set(name, items):
                f.write(json.dumps(r) + "\n")
    src = SC / "gpt4v_direct.responses.jsonl" if stored else resp
    cmd = [sys.executable, str(HERE / "score.py"), str(src), str(out), "--jobs", str(jobs)]
    if name == "gold":  # keep renders to measure fidelity against the published screenshots
        shutil.rmtree(SC / "gold_work", ignore_errors=True)
        cmd += ["--work-dir", str(SC / "gold_work")]
    subprocess.run(cmd, check=True)
    if not stored:
        resp.unlink()  # regenerable from refs/; keep only the scored output


def render_fidelity(items):
    import numpy as np
    from PIL import Image
    rows = []
    for k, it in enumerate(items):
        stem = re.sub(r"[^A-Za-z0-9_-]", "_", it["item"])
        a = np.asarray(Image.open(SC / "gold_work" / f"{k:05d}" / "ref" / f"{stem}.png").convert("RGB")).astype(int)
        b = np.asarray(Image.open(HERE / it["gold"]["screenshot"]).convert("RGB")).astype(int)
        same = a.shape == b.shape
        d = np.abs(a - b).max(axis=2) if same else None
        webfont = "@font-face" in (HERE / it["gold"]["ref_html"]).read_text(errors="replace")
        rows.append({"item": it["item"], "same_size": same, "height_delta": int(a.shape[0] - b.shape[0]),
                     "max_channel_diff": int(d.max()) if same else None,
                     "frac_pixels_off_by_gt64": round(float((d > 64).mean()), 5) if same else None,
                     "uses_font_face": webfont})
    same = [r for r in rows if r["same_size"]]
    near = [r for r in same if r["frac_pixels_off_by_gt64"] < 0.001]
    rest = [r for r in rows if r not in near]
    return {"what": "reference HTML re-rendered by the scorer (offline) vs the published screenshot shown to the model",
            "n": len(rows), "same_size": len(same),
            "identical_up_to_antialiasing (same size, every channel diff <= 64)": sum(r["max_channel_diff"] <= 64 for r in same),
            "near_identical (same size, <0.1% of pixels off by >64)": len(near),
            "rest": len(rest), "rest_using_@font-face_web_fonts": sum(r["uses_font_face"] for r in rest),
            "same_size_max_frac_pixels_off_by_gt64": max(r["frac_pixels_off_by_gt64"] for r in same),
            "height_mismatch_px_item": sorted([(r["height_delta"], r["item"]) for r in rows if not r["same_size"]])}


def describe(rows, thr):
    s = [r["score"] for r in rows]
    q = st.quantiles(s, n=10)
    return {"n": len(rows), "pass": sum(x >= thr for x in s), "pass_rate": round(sum(x >= thr for x in s) / len(s), 4),
            "score_mean": round(st.mean(s), 4), "score_median": round(st.median(s), 4), "score_min": round(min(s), 4),
            "score_p10": round(q[0], 4), "score_p90": round(q[-1], 4), "score_max": round(max(s), 4),
            "sub_means": {k: round(st.mean(r[k] for r in rows), 4) for k in SUBS},
            "official_pipeline_mean": round(st.mean(r["score_official_pipeline"] for r in rows), 4),
            "repetition_truncated": sum(r["repetition_truncated"] for r in rows),
            "scorer_errors": sum(not r["scorer_ok"] for r in rows), "html_found": sum(r["html_found"] for r in rows),
            "seconds_median": round(st.median(r["seconds"] or 0 for r in rows), 1),
            "seconds_max": round(max(r["seconds"] or 0 for r in rows), 1)}


def ranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def compare_official(rows):
    off = json.load(open(SC / "gpt4v_direct.official_scores.json"))["scores"]
    rows = [r for r in rows if r["item"] in off]
    out = {"n": len(rows), "what": "this scorer on the official GPT-4V direct-prompting predictions vs the official released per-item scores"}
    for k in ("score",) + SUBS:
        a, b = [r[k] for r in rows], [off[r["item"]][k] for r in rows]
        out[k] = {"official_mean": round(st.mean(b), 4), "ours_mean": round(st.mean(a), 4),
                  "pearson": round(st.correlation(a, b), 4), "spearman": round(st.correlation(ranks(a), ranks(b)), 4),
                  "mean_abs_diff": round(st.mean(abs(x - y) for x, y in zip(a, b)), 4)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", default=",".join(ALL_SETS))
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    SC.mkdir(exist_ok=True)
    items = [json.loads(l) for l in open(HERE / "items.jsonl")]
    for name in a.sets.split(","):
        if name == "gold_rerun" and score.THRESHOLD is None:
            continue  # run after calibration, with the final score.py
        run_set(name, items, a.jobs, a.force)
    load = lambda n: [json.loads(l) for l in open(SC / f"{n}.out.jsonl")] if (SC / f"{n}.out.jsonl").exists() else None
    res = {n: load(n) for n in ALL_SETS}
    med = {n: st.median(r["score"] for r in res[n]) for n in ("gold", "wrong_unrelated", "partial_text")}
    proposed = round(med["gold"] - (med["gold"] - med["partial_text"]), 3)
    if score.THRESHOLD is None:
        sys.exit(f"calibration: medians {med} -> THRESHOLD {proposed}; set it in score.py")
    thr = score.THRESHOLD
    report = {
        "threshold": thr,
        "calibration": {"rule": "THRESHOLD = G - margin; G = median gold self-score; margin = G - P, P = median score of the "
                                "design-free copy of the target (partial_text: its exact visible text as plain <p>, no styling, "
                                "layout or images). A pass keeps more of the target's design than a text-only transcription does.",
                        "G_median_gold": round(med["gold"], 4), "P_median_partial_text": round(med["partial_text"], 4),
                        "median_wrong_unrelated": round(med["wrong_unrelated"], 4), "proposed": proposed,
                        "alternative_not_used": f"midpoint gold/unrelated = {round((med['gold'] + med['wrong_unrelated']) / 2, 3)}",
                        "note": "passed/threshold fields in selfcheck/*.out.jsonl were recomputed from `score` with this "
                                "THRESHOLD after calibration; gold_rerun was produced end to end by the final score.py"},
        "primary_outcome": "continuous `score`; compare paired per-item means between arms. `passed` = score >= threshold (secondary).",
        "sets": {n: describe(rows, thr) for n, rows in res.items() if rows},
        "gold_failures": [{k: r[k] for k in ("item", "score", "score_official_pipeline", "error", "warnings")}
                          for r in res["gold"] if r["score"] < thr],
        "wrong_passes": {n: [(r["item"], round(r["score"], 4)) for r in res[n] if r["score"] >= thr]
                         for n in ("wrong_unrelated", "wrong_blank", "wrong_prose")},
        "extraction_tests": extraction_tests(),
    }
    if res["gpt4v_official"]:
        report["official_reproduction"] = compare_official(res["gpt4v_official"])
    if res["gold_rerun"]:
        g, h = {r["item"]: r for r in res["gold"]}, {r["item"]: r for r in res["gold_rerun"]}
        diffs = [abs(g[i]["score"] - h[i]["score"]) for i in g]
        report["determinism"] = {"items": len(diffs), "identical_scores": sum(d == 0 for d in diffs),
                                 "max_abs_diff": max(diffs),
                                 "gold_rerun_passed_field_sum": sum(r["passed"] for r in res["gold_rerun"])}
    if (SC / "gold_work").exists():
        report["render_fidelity"] = render_fidelity(items)
    (HERE / "selfcheck.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({n: (d["pass"], d["n"], d["score_median"]) for n, d in report["sets"].items()}))


if __name__ == "__main__":
    main()

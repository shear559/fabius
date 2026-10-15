#!/usr/bin/env python3
"""Score Design2Code responses with the OFFICIAL automatic visual metrics.

usage: python score.py responses.jsonl out.jsonl [--jobs 6] [--timeout 3600] [--keep-work | --work-dir DIR]
  Needs Docker (image fabius-design2code-scorer:1.0 is built from scorer/ on first use) and
  only the Python standard library on the host.
  responses.jsonl: {"item": id, "response": model text}   (one line per response)
  out.jsonl:       {"item", "passed", "score", "block_match", "text", "position", "color",
                    "clip", "score_official_pipeline", "repetition_truncated",
                    "html_found", "html_chars", "scorer_ok", "error", "warnings", ...}

Pipeline per response (all deterministic):
  1. extract_html(): explicit fence-aware rule, then the official cleanup_response().
  2. In an offline container (--network none, non-root, no capabilities) the official
     Design2Code.metrics.visual_score.visual_eval_v3_multi([[pred.html], ref.html]) runs:
     official pre_process of the prediction, Playwright/Chromium full-page renders of
     prediction AND reference (1280px viewport), OCR-free text-block detection, block
     matching, and the five scores; score = 0.2*(block_match+text+position+color+clip).
  3. An exception inside the official code (its catch-all is commented out at the pinned
     commit) or the per-item wall-clock cap gives all-zero scores, as the official
     driver's "didn't get a score" branch does; scorer_ok=false and error say why.

PRIMARY outcome = the continuous `score` (compare paired means across arms). It is the
official metric with ONE preprocessing step skipped: the repetition heuristic
(check_repetitive_content), which truncates "repetitive" predictions. It never fires on the
484 official GPT-4V outputs, but it truncated 47/80 gold references (pretty-printed
whitespace counts as repetition) to near-blank pages; see selfcheck.json.
`score_official_pipeline` keeps that step (= `score` whenever `repetition_truncated` is false).
`passed` (secondary, 0/1) = score >= THRESHOLD, see README.md and selfcheck.json.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = "fabius-design2code-scorer:1.0"
# passed = score >= THRESHOLD = G - margin, G = 1.000 (median gold self-score). margin = G - P = 0.194,
# P = 0.806 = median score of the design-free copy of the target (its exact visible text as plain <p>,
# no styling/layout/images): a pass keeps more of the design than that. Unrelated pages: median 0.517,
# max 0.753, so all fail. Calibration in selfcheck.json.
THRESHOLD = 0.806


def cleanup_response(response):
    """Verbatim from Design2Code/prompting/gpt4v_utils.py @7a575e4 (official post-processing)."""
    ## simple post-processing
    if response[ : 3] == "```":
        response = response[3 :].strip()
    if response[-3 : ] == "```":
        response = response[ : -3].strip()
    if response[ : 4] == "html":
        response = response[4 : ].strip()

    ## strip anything before '<!DOCTYPE'
    if '<!DOCTYPE' in response:
        response = response.split('<!DOCTYPE', 1)[1]
        response = '<!DOCTYPE' + response

    ## strip anything after '</html>'
    if '</html>' in response:
        response = response.split('</html>')[0] + '</html>'
    return response


HTML_MARK = re.compile(r"<html|<!doctype|<body", re.I)


def fenced_blocks(text):
    """Contents of ``` fenced blocks; an unterminated last fence runs to the end of text."""
    blocks, cur, inside = [], [], False
    for line in text.split("\n"):
        s = line.strip()
        if not inside and s.startswith("```"):
            inside, cur = True, []
        elif inside and s.startswith("```") and not s.strip("`").strip():
            blocks.append("\n".join(cur))
            inside = False
        elif inside:
            cur.append(line)
    if inside and cur:
        blocks.append("\n".join(cur))
    return blocks


def extract_html(response):
    """Rule: the longest ``` fenced block that contains <html, <!doctype or <body
    (case-insensitive); if there is none, the whole response. Then the official
    cleanup_response(). Whatever text results is scored, as in the official pipeline."""
    response = response or ""
    cands = [b for b in fenced_blocks(response) if HTML_MARK.search(b)]
    text = max(cands, key=len) if cands else response
    return cleanup_response(text.strip())


def ensure_image():
    if subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True).returncode != 0:
        print(f"building {IMAGE} (one-time, needs network) ...", file=sys.stderr)
        subprocess.run(["docker", "build", "-t", IMAGE, str(HERE / "scorer")], check=True)


def run_container(work, jobs, timeout):
    cmd = ["docker", "run", "--rm", "--init", "--network", "none", "--cap-drop", "ALL",
           "--security-opt", "no-new-privileges", "--pids-limit", "4096", "--memory", "7g",
           "--shm-size", "2g", "-v", f"{work}:/work", IMAGE,
           "python", "/opt/d2c/run_metric.py", "/work/manifest.json", "/work/results.jsonl",
           "--jobs", str(jobs), "--timeout", str(timeout)]
    r = subprocess.run(cmd, stdout=sys.stderr)
    if r.returncode != 0:  # infrastructure failure: never turn this into zero scores
        sys.exit(f"scorer container failed (exit {r.returncode}); no output written")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("responses")
    ap.add_argument("out")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=3600, help="per-item wall-clock cap (s)")
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--work-dir", help="use (and keep) this work directory")
    a = ap.parse_args()

    gold = {}
    with open(HERE / "items.jsonl") as f:
        for line in f:
            it = json.loads(line)
            gold[it["item"]] = it["gold"]
    rows = [json.loads(l) for l in open(a.responses) if l.strip()]
    unknown = [r["item"] for r in rows if r["item"] not in gold]
    if unknown:
        sys.exit(f"unknown items in responses: {unknown[:5]}")

    ensure_image()
    if a.work_dir:
        work, a.keep_work = Path(a.work_dir).resolve(), True
        work.mkdir(parents=True)
    else:
        (HERE / ".work").mkdir(exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="run-", dir=HERE / ".work"))
    rick = HERE / "refs" / "rick.jpg"
    manifest, meta = [], {}
    for n, r in enumerate(rows):
        key = f"{n:05d}"
        stem = re.sub(r"[^A-Za-z0-9_-]", "_", str(r["item"]))
        html = extract_html(r.get("response"))
        for sub in ("pred", "ref"):
            (work / key / sub).mkdir(parents=True)
            shutil.copyfile(rick, work / key / sub / "rick.jpg")
        (work / key / "pred" / f"{stem}.html").write_text(html, encoding="utf-8", errors="replace")
        shutil.copyfile(HERE / gold[r["item"]]["ref_html"], work / key / "ref" / f"{stem}.html")
        manifest.append({"key": key, "dir": f"/work/{key}", "pred_html": f"/work/{key}/pred/{stem}.html",
                         "ref_html": f"/work/{key}/ref/{stem}.html"})
        meta[key] = {"item": r["item"], "html_found": bool(HTML_MARK.search(html)), "html_chars": len(html)}
    (work / "manifest.json").write_text(json.dumps(manifest))

    run_container(work, a.jobs, a.timeout)
    results = {}
    with open(work / "results.jsonl") as f:
        for line in f:
            res = json.loads(line)
            results[res["key"]] = res
    missing = [k for k in meta if k not in results]
    if missing:
        sys.exit(f"no result for {len(missing)} responses; no output written")

    subs = ("block_match", "text", "position", "color", "clip")
    with open(a.out, "w") as f:
        for key, m in meta.items():
            res = results[key]
            trunc = bool(res.get("repetition_truncated"))
            official = float(res["score"]) if res.get("ok") else 0.0
            # primary run: the untruncated prediction when the repetition heuristic fired
            prim = (res.get("no_dedup") or {}) if trunc else res
            ok = "score" in prim
            score = float(prim["score"]) if ok else 0.0
            err = None if ok else (prim.get("error") or res.get("error") or "no score")
            row = {"item": m["item"],
                   "passed": int(THRESHOLD is not None and score >= THRESHOLD),
                   "score": score,
                   **{s: (float(prim[s]) if ok else 0.0) for s in subs},
                   "score_official_pipeline": official,
                   "repetition_truncated": trunc,
                   "html_found": m["html_found"], "html_chars": m["html_chars"],
                   "scorer_ok": ok, "error": err,
                   "warnings": res.get("warnings", []), "seconds": res.get("seconds"),
                   "pred_png_size": res.get("pred_png_size"), "ref_png_size": res.get("ref_png_size"),
                   "threshold": THRESHOLD}
            f.write(json.dumps(row) + "\n")
    if not a.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    print(f"scored {len(meta)} responses -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()

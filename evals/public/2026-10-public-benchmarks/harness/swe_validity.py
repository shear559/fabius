#!/usr/bin/env python3
"""Validity check for SWE-bench Verified Mini through the full production pipeline (PROTOCOL.md v1.1).

For every instance whose official image is present: pin the image by digest; (a) apply the
gold patch to a prepared workspace, extract it with the production code and score it with
the official harness — it must resolve; (b) start the production container on an untouched
workspace, run one wrapper command, extract — the patch must be empty — and score the
untouched base in the harness's no-patch mode — it must not resolve.

Writes swebench-image-digests.json, swebench-mini-rows-pinned.json and swebench-validity.json.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import swe_prepare as sp  # noqa: E402

ROOT = Path(os.path.expanduser("~/Documents/fabius-benchmark"))
PY = str(ROOT / ".venv/bin/python")


def present_images(rows):
    have = set(subprocess.run([sp.DOCKER, "images", "--format", "{{.Repository}}:{{.Tag}}"], capture_output=True,
                              text=True).stdout.split())
    return [r for r in rows if r["image"] in have]


def main():
    rows = json.load(open(ROOT / "swebench-mini-official-rows.json"))
    digests_path, valid_path = ROOT / "swebench-image-digests.json", ROOT / "swebench-validity.json"
    digests = json.load(open(digests_path)) if digests_path.exists() else {}
    validity = json.load(open(valid_path)) if valid_path.exists() else {}
    todo = [r for r in present_images(rows) if r["instance_id"] not in validity or
            not (ROOT / "validity-gold-patches" / f"{r['instance_id']}.diff").exists()]
    print(f"{len(todo)} instances to validate", flush=True)
    for r in todo:
        digests[r["instance_id"]] = sp.image_digest(r["image"])
    digests_path.write_text(json.dumps(digests, indent=1))
    pinned = [{**r, "image": digests.get(r["instance_id"], r["image"])} for r in rows]
    pinned_path = ROOT / "swebench-mini-rows-pinned.json"
    pinned_path.write_text(json.dumps(pinned))
    def prepare_one(r):
        iid, ref = r["instance_id"], digests[r["instance_id"]]
        log = {}
        # (a) gold through the pipeline
        root, repo, ok_a = sp.prepare_workspace(ref, r["base_commit"], log)
        gold_ok_apply, gold_patch = False, ""
        if ok_a:
            ap = subprocess.run(["git", "-C", str(repo), "apply", "-"], input=r["patch"], text=True, capture_output=True)
            gold_ok_apply = ap.returncode == 0
            gold_patch, _ = sp.extract_patch(repo, log["workspace_asserts"]["head"])
            log["gold_extracted_equals_gold_files"] = sorted(
                l.split(" b/")[-1] for l in gold_patch.splitlines() if l.startswith("diff --git")) == sorted(
                l.split(" b/")[-1] for l in r["patch"].splitlines() if l.startswith("diff --git"))
        sp.cleanup(root)
        # (b) untouched workspace through the production container and wrapper
        log_b = {}
        root, repo, ok_b = sp.prepare_workspace(ref, r["base_commit"], log_b)
        empty_patch = None
        if ok_b:
            cname, _ = sp.start_container(ref, repo)
            wrapper = sp.write_wrapper(root, cname)
            w = subprocess.run([str(wrapper), "git status"], capture_output=True, text=True, timeout=300)
            log["wrapper_exit"] = w.returncode
            sp.kill_container(cname)
            empty_patch, _ = sp.extract_patch(repo, log_b["workspace_asserts"]["head"])
        sp.cleanup(root)
        (ROOT / "validity-gold-patches").mkdir(exist_ok=True)
        (ROOT / "validity-gold-patches" / f"{iid}.diff").write_text(gold_patch)
        return iid, {"workspace_ok": ok_a and ok_b, "gold_applied": gold_ok_apply, "empty_patch_is_empty": empty_patch == "",
                     **log, "valid": None}

    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(4) as ex:
        for iid, v in ex.map(prepare_one, todo):
            validity[iid] = v
            print(iid, "workspace", v["workspace_ok"], "gold applied", v["gold_applied"], "empty", v["empty_patch_is_empty"],
                  flush=True)
            valid_path.write_text(json.dumps(validity, indent=1))
    pending = [iid for iid, v in validity.items() if v.get("valid") is None]
    preds = []
    for iid in pending:
        gp = ROOT / "validity-gold-patches" / f"{iid}.diff"
        if gp.exists() and gp.read_text().strip():
            preds.append({"instance_id": iid, "model_name_or_path": "gold-pipeline", "model_patch": gp.read_text()})
    if not preds:
        return
    ppath = ROOT / "validity-gold-preds.jsonl"
    ppath.write_text("".join(json.dumps(p) + "\n" for p in preds))
    ids = pending
    run_id = "validity-gold"
    subprocess.run([PY, "-m", "swebench.harness.run_evaluation", "-d", str(pinned_path), "-p", str(ppath),
                    "-id", run_id, "--max_workers", "2", "-i", *ids], cwd=ROOT / "eval", check=False)
    # untouched base, the harness's no-patch mode
    no_patch = subprocess.run([PY, str(ROOT / "harness/swe_nopatch.py"), str(pinned_path), *ids],
                              capture_output=True, text=True, cwd=ROOT / "eval")
    base_resolved = json.loads(no_patch.stdout.strip().splitlines()[-1]) if no_patch.returncode == 0 else {}
    for iid in ids:
        rep = ROOT / "eval/logs/run_evaluation" / run_id / "gold-pipeline" / iid / "report.json"
        gold_resolved = json.loads(rep.read_text())[iid]["resolved"] if rep.exists() else None
        v = validity[iid]
        v["gold_resolved"] = gold_resolved
        v["base_resolved"] = base_resolved.get(iid)
        v["valid"] = bool(v["workspace_ok"] and v["gold_applied"] and v["empty_patch_is_empty"] and gold_resolved
                          and v["base_resolved"] is False)
        print(iid, "gold resolved", gold_resolved, "base resolved", v["base_resolved"], "VALID" if v["valid"] else "INVALID")
    valid_path.write_text(json.dumps(validity, indent=1))
    print("rows file sha256:", hashlib.sha256(pinned_path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()

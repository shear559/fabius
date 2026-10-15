#!/usr/bin/env python3
"""Freeze existing benchmark inputs without running a preparer or reading old outcomes.

The manifest is PRIVATE: it contains scorer metadata and local source locations.
Only ``runtime_task`` may cross into the generation runtime. Asset ``source`` paths
are for the controller's copy operation; the model sees only their relative names.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

ARMS = ("baseline", "old", "candidate")
SKILLS = {
    "swebench": "disciplina", "ifeval": "fabius", "humaneval": "parcus",
    "cyberseceval": "praesidium", "labbench": "scientia", "finqa": "fortuna",
    "ds1000": "doctrina", "smartbugs": "catena", "bfcl": "cohors",
    "longmemeval": "archivum", "design2code": "decor",
}
COUNTS = dict(zip(SKILLS, (50, 541, 163, 200, 220, 200, 200, 143, 200, 120, 80)))
METRICS = {b: ("continuous" if b == "design2code" else "binary") for b in SKILLS}
EVALPLUS_INSTRUCTION = (
    "Please provide a self-contained Python script that solves the following "
    "problem in a markdown code block:"
)
HE32_REASON = "Canonical solution fails the registered EvalPlus sandbox validity check."


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def item_key(benchmark, item_id, sample=1):
    """A collision-free identity; item IDs can contain slashes or underscores."""
    return canonical([benchmark, str(item_id), int(sample)])


def arm_order(seed, benchmark, item_id, sample):
    """Hash-ranking is a deterministic random permutation, independent of RNG versions."""
    return sorted(ARMS, key=lambda a: digest(canonical([seed, benchmark, str(item_id), sample, a])))


def _under(root, relative):
    rel = PurePosixPath(str(relative))
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("Input paths must stay within data_root")
    path = (root / str(rel)).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Input symlink escapes data_root")
    return path


def _unique(rows, key):
    result = {}
    for row in rows:
        ident = str(row[key])
        if ident in result:
            raise ValueError(f"Duplicate input identifier: {ident}")
        result[ident] = row
    return result


def build_manifest(data_root, seed=20261010, legacy_public_root=None):
    """Read only prepared inputs, schedules, validity metadata, and source pins.

    ``legacy_public_root``, when supplied, verifies the published Part B input
    hashes too. Counts, selection, and the intrinsic HumanEval exclusion are fixed.
    IFEval 143 is retried: its old infrastructure failure is not item invalidity.
    """
    root = Path(data_root).resolve(strict=True)
    sources = {}

    def read(relative, kind="json"):
        data = _under(root, relative).read_bytes()
        sources[relative] = digest(data)
        if kind == "bytes":
            return data
        if kind == "jsonl":
            return [json.loads(line) for line in data.decode().splitlines() if line.strip()]
        return json.loads(data)

    published = read("schedule.json")
    part_b = read("schedule-skills.json")
    swe_rows = _unique(read("swebench-mini-official-rows.json"), "instance_id")
    validity = read("swebench-validity.json")
    images = read("swebench-image-digests.json")
    if legacy_public_root is not None:
        legacy = Path(legacy_public_root)
        for filename, current in (("schedule.json", published), ("schedule-skills.json", part_b)):
            prior = json.loads((legacy / filename).read_text())
            for benchmark, value in prior.items():
                if isinstance(value, dict) and "items" in value:
                    if current.get(benchmark, {}).get("items") != value["items"]:
                        raise ValueError(f"{benchmark}: item order differs from published schedule")
        pinned = read("swebench-mini-rows-pinned.json")
        expected_hash = (legacy / "swebench/rows-sha256.txt").read_text().split()[0]
        if sources["swebench-mini-rows-pinned.json"] != expected_hash:
            raise ValueError("SWE pinned dataset differs from published hash")
        for row in pinned:
            current = swe_rows.get(row["instance_id"], {})
            if any(current.get(k) != row[k] for k in ("problem_statement", "base_commit")):
                raise ValueError("SWE current task differs from the published pinned input")
        prior_validity = json.loads((legacy / "swebench/swebench-validity.json").read_text())
        if {i for i, v in validity.items() if v.get("valid")} != {i for i, v in prior_validity.items() if v.get("valid")}:
            raise ValueError("SWE validity set differs from published exclusions")
    all_items, schedule, prerequisites = [], [], {}
    exclusions = {"humaneval": {"HumanEval_32": HE32_REASON}, "swebench": {}}

    for benchmark, skill in SKILLS.items():
        if benchmark == "swebench":
            rows = swe_rows
            order = [str(i) for i in published[benchmark]["items"]]
            exclusions[benchmark] = {i: "Failed the registered pre-generation validity check"
                                     for i in order if not validity.get(i, {}).get("valid")}
            order = [i for i in order if validity.get(i, {}).get("valid")]
        elif benchmark == "ifeval":
            rows = _unique(read("ifeval/instruction_following_eval/data/input_data.jsonl", "jsonl"), "key")
            order = [str(i) for i in published[benchmark]["items"]]
        elif benchmark == "humaneval":
            original = read("humanevalplus/cache/HumanEvalPlus-v0.1.10.jsonl", "jsonl")
            rows = _unique([dict(row, item=row["task_id"].replace("/", "_")) for row in original], "item")
            order = [str(i) for i in published[benchmark]["items"]]
            if "HumanEval_32" in order:
                raise ValueError("Published schedule unexpectedly includes invalid HumanEval_32")
        else:
            relative = f"skills-bench/{benchmark}/items.jsonl"
            original = read(relative, "jsonl")
            rows = _unique(original, "item")
            source = read(f"skills-bench/{benchmark}/source.json")
            if legacy_public_root is not None:
                pin = Path(legacy_public_root) / "skills" / benchmark / "items.sha256"
                expected = pin.read_text().split()[0]
                if sources[relative] != expected:
                    raise ValueError(f"{benchmark}: prepared inputs differ from published hash")
            if benchmark in part_b:
                order = [str(i) for i in part_b[benchmark]["items"]]
            else:
                # These prepared, seeded selections were never run in Part B.
                sampling = source["sampling"]
                selected = sampling.get("sampled_ids_in_order", sampling.get("ids"))
                if [str(i) for i in selected] != list(rows):
                    raise ValueError(f"{benchmark}: prepared selection differs from source pin")
                order = list(rows)
            if set(order) != set(rows):
                raise ValueError(f"{benchmark}: published schedule differs from prepared selection")

        if len(order) != COUNTS[benchmark] or len(set(order)) != len(order):
            raise ValueError(f"{benchmark}: wrong number of unique selected items")
        if set(order) - set(rows):
            raise ValueError(f"{benchmark}: schedule references missing input")
        samples = (1, 2) if benchmark == "swebench" else (1,)
        for sample in samples:
            for ident in order:
                row, assets = rows[ident], []
                prompt = row.get("prompt", row.get("problem_statement", ""))
                if benchmark == "humaneval":
                    prompt = EVALPLUS_INSTRUCTION + f"\n```python\n{row['prompt'].strip()}\n```\n"
                scorer_data = {"row": row}
                if benchmark == "swebench":
                    scorer_data.update(image=images[ident], validity=validity[ident])
                if benchmark == "design2code":
                    gold = row["gold"]
                    png = f"skills-bench/{benchmark}/{gold['screenshot']}"
                    data = read(png, "bytes")
                    if digest(data) != gold["screenshot_sha256"]:
                        raise ValueError("Design2Code screenshot hash mismatch")
                    destination = "input/screenshot.png"
                    # Replace only the registered local-path slot, never task content.
                    prompt, n = re.subn(r"(?<=the PNG image file at )[^\n]+(?= \(view it with your file-reading tool\))",
                                        destination, prompt)
                    if n != 1:
                        raise ValueError("Design2Code image path slot was not recognized")
                    assets = [{"path": destination, "source": str(_under(root, png)),
                               "source_relative": png, "sha256": digest(data)}]
                    ref = f"skills-bench/{benchmark}/{gold['ref_html']}"
                    if digest(read(ref, "bytes")) != gold["ref_html_sha256"]:
                        raise ValueError("Design2Code reference hash mismatch")
                    read(f"skills-bench/{benchmark}/refs/rick.jpg", "bytes")
                task_input = {"prompt": prompt, "files": {},
                              "assets": [{"path": a["path"], "sha256": a["sha256"]} for a in assets]}
                key = item_key(benchmark, ident, sample)
                item = {"item_key": key, "benchmark": benchmark, "item_id": ident, "sample": sample,
                        "skill": skill, "prompt": prompt, "prompt_sha256": digest(prompt),
                        "input_sha256": digest(canonical(task_input)), "files": {}, "assets": assets,
                        "metric_kind": METRICS[benchmark], "scorer_data": scorer_data}
                all_items.append(item)
                schedule.append({"item_key": key, "benchmark": benchmark, "item_id": ident,
                                 "sample": sample, "arms": arm_order(seed, benchmark, ident, sample)})

    prerequisites["swebench"] = "Fresh pinned-image workspace, restricted execution and official patch scorer required."
    prerequisites["longmemeval"] = "Freeze judge model/settings; calibrate gold/wrong judge controls; run official two-stage judge."
    prerequisites["design2code"] = "Image-capable Read tool plus pinned offline Chromium/CLIP scorer required; primary score is continuous."
    manifest = {"schema_version": 1, "private": True, "data_root": str(root), "seed": seed,
                "arms": list(ARMS), "counts": dict(COUNTS), "source_files": sources,
                "items": all_items, "schedule": schedule, "exclusions": exclusions,
                "prerequisites": prerequisites,
                "deviations": ["IFEval 143 remains selected and is retried in the new cohort.",
                               "Design2Code local image paths are replaced with an isolated relative asset path.",
                               "All arms are contemporary; no old outcome or baseline is reused."]}
    manifest["manifest_sha256"] = digest(canonical(manifest))
    return manifest


def verify_manifest(manifest, data_root=None):
    recorded = dict(manifest)
    claimed = recorded.pop("manifest_sha256")
    if digest(canonical(recorded)) != claimed:
        raise ValueError("Manifest content hash mismatch")
    root = Path(data_root or manifest["data_root"]).resolve(strict=True)
    for relative, expected in manifest["source_files"].items():
        if digest(_under(root, relative).read_bytes()) != expected:
            raise ValueError(f"Frozen source changed: {relative}")
    for item in manifest["items"]:
        if digest(item["prompt"]) != item["prompt_sha256"]:
            raise ValueError("Frozen prompt changed")
        visible = {"prompt": item["prompt"], "files": item["files"],
                   "assets": [{"path": a["path"], "sha256": a["sha256"]} for a in item["assets"]]}
        if digest(canonical(visible)) != item["input_sha256"]:
            raise ValueError("Frozen task input changed")
    return True


def runtime_task(item):
    """Allowlisted generation input: never copy private gold, references or scorer data."""
    skill = item["skill"]
    return {"id": item["item_key"], "prompt": item["prompt"],
            "specialist": "fabius" if skill == "fabius" else f"fabius-{skill}",
            "files": dict(item["files"]),
            "assets": [{k: a[k] for k in ("path", "source", "sha256")} for a in item["assets"]],
            "profile": "swe" if item["benchmark"] == "swebench" else "read_only"}


def write_manifest(manifest, path):
    """Freeze once; an existing different manifest is never overwritten."""
    path = Path(path).resolve()
    public_repo = Path(__file__).resolve().parents[3]
    if path.is_relative_to(public_repo) or path.is_relative_to(Path(manifest["data_root"]).resolve()):
        raise ValueError("Private manifests must be outside the public repository and read-only data_root")
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text() != text:
            raise FileExistsError("A different manifest is already frozen at this path")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        handle.write(text)
    path.chmod(0o600)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--out", required=True, help="PRIVATE manifest destination, outside the public repository")
    ap.add_argument("--legacy-public-root")
    ap.add_argument("--seed", type=int, default=20261010)
    args = ap.parse_args()
    manifest = build_manifest(args.data_root, args.seed, args.legacy_public_root)
    verify_manifest(manifest)
    write_manifest(manifest, args.out)
    print(json.dumps({"counts": manifest["counts"], "blocks": len(manifest["schedule"]),
                      "manifest_sha256": manifest["manifest_sha256"]}))


if __name__ == "__main__":
    main()

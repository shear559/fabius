#!/usr/bin/env python3
"""Build the two frozen, filtered model-visible packages of the continuation from INPUTS.json.

  build_packages.py <INPUTS.json> <fabius repo> [--out /private/tmp/fbpkg]

For each package (old = v3.3.0-sealed, candidate = 6fb0ab0) every listed path is extracted from the named
commit with `git show`, written under <out>/<name>/fabius/, and its SHA-256 and size are checked against
the manifest. The manifest digest is recomputed as Codex's items.py defines it (sha256 of the files list as
compact key-sorted JSON) and must equal INPUTS.json's. A package with any file mismatch is deleted and the build fails.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    inputs = json.load(open(sys.argv[1]))
    repo = sys.argv[2]
    out = Path(sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "/private/tmp/fbpkg")
    report = {}
    for name, pk in inputs["packages"].items():
        dest = out / name / "fabius"
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        commit = pk["source_commit"]
        bad = []
        lines = []
        for f in pk["files"]:
            blob = subprocess.run(["git", "-C", repo, "show", f"{commit}:{f['path']}"], capture_output=True, check=True).stdout
            digest = hashlib.sha256(blob).hexdigest()
            if digest != f["sha256"] or len(blob) != f["bytes"]:
                bad.append(f["path"])
            target = dest / f["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
            lines.append(f"{digest}  {f['path']}\n")
        # INPUTS.json's digest: sha256 of the files list as compact, key-sorted JSON (Codex's canonical form)
        manifest_digest = hashlib.sha256(json.dumps(pk["files"], sort_keys=True, ensure_ascii=False,
                                                    separators=(",", ":")).encode()).hexdigest()
        skills = sorted(p.parent.name for p in dest.glob("skills/*/SKILL.md"))
        report[name] = {"commit": commit, "files": len(pk["files"]), "file_mismatches": bad, "skills": len(skills),
                        "manifest_sha256_inputs": pk["manifest_sha256"], "manifest_sha256_recomputed": manifest_digest,
                        "manifest_digest_matches": manifest_digest == pk["manifest_sha256"], "dir": str(dest)}
        if bad:
            shutil.rmtree(dest)
    print(json.dumps(report, indent=1))
    (out / "build-report.json").write_text(json.dumps(report, indent=1))
    sys.exit(1 if any(r["file_mismatches"] or not r["manifest_digest_matches"] for r in report.values()) else 0)


if __name__ == "__main__":
    main()

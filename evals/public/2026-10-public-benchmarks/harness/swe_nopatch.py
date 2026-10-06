#!/usr/bin/env python3
"""Score the untouched base commit with the official harness's no-patch mode.

  swe_nopatch.py <rows.json> <instance_id>...   (prints a JSON map instance_id -> resolved)
"""
import json
import sys

import docker
from swebench.harness.run_evaluation import run_instance
from swebench.harness.utils import make_test_spec


def main():
    rows = {r["instance_id"]: r for r in json.load(open(sys.argv[1]))}
    client = docker.from_env()
    out = {}
    for iid in sys.argv[2:]:
        spec = make_test_spec(rows[iid])
        pred = {"instance_id": iid, "model_name_or_path": "base-no-patch", "model_patch": ""}
        try:
            _, report = run_instance(spec, pred, client, "validity-base", timeout=1800, skip_patch=True)
            out[iid] = bool(report and report.get(iid, {}).get("resolved"))
        except Exception as e:  # report the failure; the instance will not count as valid
            out[iid] = None
            print(f"{iid}: no-patch scoring failed: {e}", file=sys.stderr)
    print(json.dumps(out))


if __name__ == "__main__":
    main()

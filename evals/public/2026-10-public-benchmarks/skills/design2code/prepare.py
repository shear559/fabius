#!/usr/bin/env python3
"""Build the Design2Code harness inputs: items.jsonl, source.json, screenshots/, refs/.

1. List SALT-NLP/Design2Code at a pinned HF revision; eligible ids = file stems that have
   both <id>.html and <id>.png (484). Sort them (string sort), permute with
   numpy.random.default_rng(20261006).permutation, keep the first N=80.
2. Download those pairs + rick.jpg; copy to screenshots/<id>.png (shown to the model)
   and refs/<id>.html (+ refs/rick.jpg) (re-rendered by the official metric).
3. Vendor the official metric code (NoviScl/Design2Code at a pinned commit) into
   scorer/official/ and apply the whitespace-only IndentationError fix.
4. Optionally (--build-image) build the offline scorer image used by score.py.

usage: python prepare.py [--image-root DIR] [--build-image]
  --image-root: directory whose absolute path is written into the prompts (default:
  ./screenshots). Use it to relocate the PNGs; they are copied there.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(HERE / ".hf_home"))  # keep HF caches inside this harness

import numpy as np  # noqa: E402
from huggingface_hub import HfApi, hf_hub_download  # noqa: E402

HF_REPO = "SALT-NLP/Design2Code"
HF_REV = "e2f61f6e9d9b5ee201b81d8e0ae4d37aa13f8f25"
GH_REPO = "NoviScl/Design2Code"
GH_SHA = "7a575e4c33f417c4be5c64072b8f5798de0d0f99"
SEED, N = 20261006, 80
IMAGE = "fabius-design2code-scorer:1.0"
BASE_IMAGE = "python@sha256:0a310eeecf4e1f5a0743f9a6520c90c88d089c903ca5fd283f501e3a805f5f89"

# SHA-256 of the official files at GH_SHA (verified on download).
OFFICIAL_FILES = {
    "Design2Code/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "Design2Code/metrics/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "Design2Code/metrics/visual_score.py": "be04fc266b8a992f224afd11771d1f9b7ff9a30eefb3a9f65e8c6762115d1f54",
    "Design2Code/metrics/ocr_free_utils.py": "8ac528d2ca702d316a4c4594dd5f58a78b9f9e76a1ca5daaf320f15355c4446f",
    "Design2Code/metrics/screenshot_single.py": "46b20065df5ced34d4779533e3004208f922ed6bc3554cca7584f16621ca0222",
    "Design2Code/data_utils/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "Design2Code/data_utils/dedup_post_gen.py": "9b9d6b8eb150dba575d6d322a9d997f24f4cbaef8d4a362379139b9bf56dc4e1",
}
PATCHED_VISUAL_SCORE = "e7ec08f5e5709a6db5e9b8109dbab166ee92c3a68761fe1b8a34950238e30004"

# Official direct-prompting instruction (Design2Code/prompting/gpt4v.py and claude.py),
# verbatim except line 2 (points at the screenshot file) and the last line (output form).
PROMPT_TEMPLATE = (
    "You are an expert web developer who specializes in HTML and CSS.\n"
    "A user will provide you with a screenshot of a webpage: the PNG image file at {image_path} "
    "(view it with your file-reading tool).\n"
    "You need to return a single html file that uses HTML and CSS to reproduce the given website.\n"
    "Include all CSS code in the HTML file itself.\n"
    "If it involves any images, use \"rick.jpg\" as the placeholder.\n"
    "Some images on the webpage are replaced with a blue rectangle as the placeholder, use \"rick.jpg\" for those as well.\n"
    "Do not hallucinate any dependencies to external files. You do not need to include JavaScript scripts for dynamic interactions.\n"
    "Pay attention to things like size, text, position, and color of all the elements, as well as the overall layout.\n"
    "Respond with the content of the HTML+CSS file, as one complete HTML document in a single ```html code block:\n"
)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", path
    return [int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")]


def fix_indentation(src):
    """Whitespace-only fix of the IndentationError that commit acaf2c6 introduced in
    visual_eval_v3_multi (lines 458-467); the token stream is unchanged."""
    lines = src.split("\n")
    i = lines.index("         if len(predict_blocks) == 0:")
    for k in range(i, i + 10):
        stripped = lines[k].lstrip(" ")
        indent = 8 if stripped.startswith(("if ", "elif ")) else 12
        lines[k] = " " * indent + stripped
    out = "\n".join(lines)
    assert out.split() == src.split()
    compile(out, "visual_score.py", "exec")
    return out


def vendor_official():
    root = HERE / "scorer" / "official"
    for rel, want in OFFICIAL_FILES.items():
        dst = root / rel
        final_want = PATCHED_VISUAL_SCORE if rel.endswith("visual_score.py") else want
        if dst.exists() and sha256(dst) == final_want:
            continue
        url = f"https://raw.githubusercontent.com/{GH_REPO}/{GH_SHA}/{rel}"
        data = urllib.request.urlopen(url, timeout=120).read()
        assert hashlib.sha256(data).hexdigest() == want, f"hash mismatch for {rel}"
        if rel.endswith("visual_score.py"):
            data = fix_indentation(data.decode()).encode()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        assert sha256(dst) == final_want, f"vendored hash mismatch for {rel}"
    return {rel: {"sha256_at_commit": want,
                  "sha256_vendored": sha256(root / rel)} for rel, want in OFFICIAL_FILES.items()}


def build_image():
    subprocess.run(["docker", "build", "-t", IMAGE, str(HERE / "scorer")], check=True)
    return subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
                          check=True, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-root", default=str(HERE / "screenshots"))
    ap.add_argument("--build-image", action="store_true")
    a = ap.parse_args()
    image_root = Path(a.image_root).resolve()

    files = HfApi().list_repo_files(HF_REPO, repo_type="dataset", revision=HF_REV)
    stems = {f[:-5] for f in files if f.endswith(".html")} & {f[:-4] for f in files if f.endswith(".png")}
    ids = sorted(stems)
    assert len(ids) == 484, len(ids)
    perm = np.random.default_rng(SEED).permutation(len(ids))
    sampled = [ids[i] for i in perm[:N]]

    cache = HERE / "data" / "hf_Design2Code"
    get = lambda name: hf_hub_download(HF_REPO, name, repo_type="dataset", revision=HF_REV, local_dir=cache)
    for d in ("screenshots", "refs"):
        (HERE / d).mkdir(exist_ok=True)
    image_root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(get("rick.jpg"), HERE / "refs" / "rick.jpg")
    file_hashes = {"rick.jpg": sha256(HERE / "refs" / "rick.jpg")}

    items = []
    for i in sampled:
        png, html = HERE / "screenshots" / f"{i}.png", HERE / "refs" / f"{i}.html"
        shutil.copyfile(get(f"{i}.png"), png)
        shutil.copyfile(get(f"{i}.html"), html)
        if image_root != png.parent:
            shutil.copyfile(png, image_root / png.name)
        file_hashes[f"{i}.png"], file_hashes[f"{i}.html"] = sha256(png), sha256(html)
        items.append({"item": i,
                      "prompt": PROMPT_TEMPLATE.format(image_path=str(image_root / f"{i}.png")),
                      "gold": {"ref_html": f"refs/{i}.html", "ref_html_sha256": file_hashes[f"{i}.html"],
                               "screenshot": f"screenshots/{i}.png", "screenshot_sha256": file_hashes[f"{i}.png"],
                               "screenshot_size": png_size(png)}})
    with open(HERE / "items.jsonl", "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    official = vendor_official()
    image_id = build_image() if a.build_image else subprocess.run(
        ["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], capture_output=True, text=True).stdout.strip()
    source = {
        "benchmark": "Design2Code (Si et al., 2024, arXiv:2403.03163), 484 real C4 webpages",
        "dataset": {"hf_repo": HF_REPO, "hf_revision": HF_REV, "license": "ODC-By 1.0 (dataset card: odc-by)",
                    "n_eligible": len(ids), "ids_sorted_sha256": hashlib.sha256("\n".join(ids).encode()).hexdigest(),
                    "file_sha256": file_hashes},
        "sampling": {"rule": "sorted(ids) as strings -> numpy.random.default_rng(20261006).permutation(484) -> first 80",
                     "seed": SEED, "n": len(sampled), "sampled_ids_in_order": sampled},
        "official_code": {"repo": f"https://github.com/{GH_REPO}", "commit": GH_SHA, "license": "MIT",
                          "files": official,
                          "modification": "visual_score.py: whitespace-only re-indent of lines 458-467 "
                                          "(IndentationError since commit acaf2c6); see scorer/official-indent-fix.patch"},
        "scoring": {"primary": "score = official visual_eval_v3_multi with its repetition-truncation pre-step "
                               "(check_repetitive_content) skipped when it fires; compare paired means",
                    "official_pipeline": "score_official_pipeline = unmodified pipeline incl. that pre-step",
                    "passed": "score >= THRESHOLD in score.py (calibration in selfcheck.json)"},
        "scorer_image": {"tag": IMAGE, "image_id": image_id or None, "base": BASE_IMAGE,
                         "chromium": "Chrome for Testing 153.0.8010.12 headless shell (playwright 1.63.0)",
                         "clip_weights": "ViT-B-32.pt sha256 40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af",
                         **{f"{p.replace('.', '_')}_sha256": sha256(HERE / "scorer" / p)
                            for p in ("Dockerfile", "requirements.lock.txt", "run_metric.py")}},
        "prompt_template": PROMPT_TEMPLATE,
        "image_root": str(image_root),
    }
    with open(HERE / "source.json", "w") as f:
        json.dump(source, f, indent=1)
    print(f"wrote {len(items)} items; first ids: {sampled[:5]}; image {image_id or 'NOT BUILT'}")


if __name__ == "__main__":
    main()

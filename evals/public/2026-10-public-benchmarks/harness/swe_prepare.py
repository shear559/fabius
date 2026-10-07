#!/usr/bin/env python3
"""SWE-bench Verified Mini: workspace, container, wrapper, patch (PROTOCOL.md v1.1, benchmark 1).

prepare_workspace(): copy /testbed out of a fresh container of the pinned image into
/private/tmp/fbw-<random>/repo; delete every tag and every ref except the current branch,
expire reflogs, prune; assert HEAD == base, rev-list --all == rev-list HEAD, no unreachable
objects, clean status. start_container(): network-less, 3 GB, the workspace mounted at
/testbed. extract_patch(): after the container is killed, git add -A and diff against the
base, excluding test paths (and the unfiltered diff as the declared secondary).
"""
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

DOCKER = "/usr/local/bin/docker"
EXCLUDES = [":(exclude).claude", ":(exclude)tests", ":(exclude)testing", ":(glob,exclude)**/test_*.py",
            ":(glob,exclude)**/*_tests.py", ":(glob,exclude)**/conftest.py"]
CONDA = "source /opt/miniconda3/bin/activate testbed >/dev/null 2>&1"
# The official images commit their environment setup on top of the base commit ("SWE-bench"):
# file modes everywhere, and for Sphinx the tox.ini / setup.py edits of the official spec.
ENV_FILES = {"tox.ini", "setup.py", "setup.cfg", "pyproject.toml"}


def sh(args, cwd=None, check=True, timeout=1800):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, args))[:200]} -> {r.returncode}: {r.stderr[:800]}")
    return r


def git(repo, *args, check=True, timeout=1800):
    return sh(["git", "-C", str(repo), *args], check=check, timeout=timeout)


def image_digest(image):
    out = sh([DOCKER, "image", "inspect", "--format", "{{json .RepoDigests}}", image]).stdout
    digests = json.loads(out)
    return digests[0] if digests else None


def prepare_workspace(image_ref, base_commit, log):
    root = Path(tempfile.mkdtemp(prefix="fbw-", dir="/private/tmp"))
    repo = root / "repo"
    # Stream /testbed out of a fresh, network-less container as a tar archive (docker cp proved
    # unreliable on macOS: "chtimes ... no such file or directory"). Up to three attempts.
    for attempt in range(3):
        shutil.rmtree(repo, ignore_errors=True)
        repo.mkdir()
        cname = f"fbcp-{uuid.uuid4().hex[:12]}"
        producer = subprocess.Popen([DOCKER, "run", "--rm", "--network", "none", "--name", cname, image_ref,
                                     "tar", "-C", "/testbed", "-cf", "-", "."], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        consumer = subprocess.run(["tar", "-C", str(repo), "-xf", "-"], stdin=producer.stdout, capture_output=True)
        producer.stdout.close()
        perr = producer.communicate(timeout=1800)[1]
        if producer.returncode == 0 and consumer.returncode == 0 and (repo / ".git").exists():
            break
        log.setdefault("copy_retries", []).append((producer.returncode, consumer.returncode,
                                                   (perr or b"").decode()[-300:], consumer.stderr.decode()[-300:]))
    else:
        raise RuntimeError(f"could not copy /testbed out of {image_ref}: {log.get('copy_retries')}")
    git(repo, "config", "core.fileMode", "false")
    for tag in git(repo, "tag", "-l").stdout.split():
        git(repo, "tag", "-d", tag)
    head_ref = git(repo, "symbolic-ref", "-q", "HEAD", check=False).stdout.strip()
    for ref in git(repo, "for-each-ref", "--format=%(refname)").stdout.split():
        if ref != head_ref:
            git(repo, "update-ref", "-d", ref)
    git(repo, "reflog", "expire", "--expire=now", "--all")
    git(repo, "-c", "gc.reflogExpire=now", "-c", "gc.reflogExpireUnreachable=now", "gc", "--prune=now", "--quiet")
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    parent = git(repo, "rev-parse", "HEAD^", check=False).stdout.strip()
    # The official images add one commit, "SWE-bench", on top of the base commit that changes
    # file modes only. The patch is taken against HEAD, the state the official harness patches.
    raw = git(repo, "diff", "--raw", "--no-renames", "--abbrev=40", base_commit, head, check=False).stdout.strip() \
        if head != base_commit else ""
    # ":<old mode> <new mode> <old blob> <new blob> <status>\t<path>" — same blob means same content
    entries = [(l.split("\t")[0].split(), l.split("\t", 1)[1]) for l in raw.splitlines() if l.startswith(":")]
    changed_paths = sorted(path for meta, path in entries if meta[2] != meta[3])
    content_changes = len(changed_paths)
    env_only = all(p in ENV_FILES for p in changed_paths)
    all_revs = sorted(git(repo, "rev-list", "--all").stdout.split())
    head_revs = sorted(git(repo, "rev-list", "HEAD").stdout.split())
    unreachable = git(repo, "fsck", "--unreachable", "--no-reflogs", "--no-progress", check=False).stdout.strip()
    status = git(repo, "status", "--porcelain").stdout.strip()
    asserts = {
        "head_is_base_or_env_child": head == base_commit or (parent == base_commit and env_only),
        "no_commit_beyond_head": all_revs == head_revs,
        "no_unreachable_objects": unreachable == "",
        "status_clean": status == "",
        "head": head, "head_parent": parent, "head_ref": head_ref, "commits_reachable": len(head_revs),
        "head_vs_base_content_changes": content_changes, "head_vs_base_changed_paths": changed_paths,
        "head_vs_base_entries": len(entries),
        "status_sample": status[:400], "unreachable_sample": unreachable[:400],
    }
    log["workspace_asserts"] = asserts
    ok = all(asserts[k] for k in ("head_is_base_or_env_child", "no_commit_beyond_head",
                                  "no_unreachable_objects", "status_clean"))
    return root, repo, ok


def start_container(image_ref, repo):
    cname = f"fbrun-{uuid.uuid4().hex[:12]}"
    args = [DOCKER, "run", "-d", "--rm", "--network", "none", "--memory", "3g", "--name", cname,
            "-v", f"{repo}:/testbed", image_ref, "sleep", "infinity"]
    sh(args)
    return cname, args


def write_wrapper(root, cname):
    wrapper = root / "run"
    wrapper.write_text(
        "#!/bin/bash\n"
        "# Runs one shell command inside this task's Linux test container, in /testbed (the same files).\n"
        f"exec {DOCKER} exec -i -w /testbed {cname} bash -lc \"{CONDA}; $*\"\n")
    wrapper.chmod(0o755)
    return wrapper


def kill_container(cname):
    sh([DOCKER, "kill", cname], check=False, timeout=120)


def extract_patch(repo, head):
    """The agent's change relative to the workspace HEAD (the state the official harness patches)."""
    git(repo, "add", "-A")
    filtered = git(repo, "-c", "core.fileMode=false", "diff", "--cached", "--binary", head, "--", ".",
                   *EXCLUDES).stdout
    unfiltered = git(repo, "-c", "core.fileMode=false", "diff", "--cached", "--binary", head, "--", ".",
                     ":(exclude).claude").stdout
    return filtered, unfiltered


def patch_size(patch):
    added = sum(1 for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in patch.splitlines() if l.startswith("-") and not l.startswith("---"))
    files = sum(1 for l in patch.splitlines() if l.startswith("diff --git "))
    return {"added": added, "removed": removed, "files": files}


def cleanup(root):
    shutil.rmtree(root, ignore_errors=True)


PROMPT_TAIL = (
    "\n\n---\n"
    "The repository for this issue is checked out in the current directory ({repo}), at the commit where the "
    "issue was reported. Its test environment is a Linux container that sees the same files at /testbed; run "
    "any shell command there with:\n\n"
    "    {wrapper} \"<command>\"\n\n"
    "for example `{wrapper} \"git status\"`. Resolve the issue by changing non-test source files. "
    "This run is non-interactive: nobody can answer questions or grant permissions; state any assumption "
    "and finish the task.")


def render_prompt(problem_statement, repo, wrapper):
    return problem_statement + PROMPT_TAIL.format(repo=repo, wrapper=wrapper)


def normalized_prompt(prompt, root):
    """The prompt with the run's random workspace root replaced, for the cross-arm identity check."""
    return prompt.replace(str(root), "<workspace>")

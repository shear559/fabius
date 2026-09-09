#!/usr/bin/env python3
"""Build and inspect a deterministic, complete Claude-compatible plugin ZIP.

Only Python's standard library and read-only Git inventory commands are used.
No bundled code, dependency installer, signing key, or upload service is invoked.
Run ``python3 scripts/distribution.py --help`` for the explicit operations.
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
import subprocess
import tempfile
import unicodedata
from urllib.parse import unquote, urlsplit
import zipfile


CONTENT_PATH = "credits/content-manifest.json"
ARCHIVE_MANIFEST = "distribution-manifest.json"
REGISTRY_PATH = "credits/upstream.json"
ZIP_DATE = (1980, 1, 1, 0, 0, 0)
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
DENIED_PARTS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".cache",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".in_use", ".wrangler",
    ".next", ".nuxt", ".gradle", ".idea", ".ds_store", ".ssh", ".aws",
}
ENV_TEMPLATES = {".env.example", ".env-example", ".env.template", ".env-template"}
SECRET_NAMES = {".npmrc", ".pypirc", ".netrc", "credentials.json",
                "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa"}
SECRET_BYTES = re.compile(
    rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----(?:\r?\n|\\n)[A-Za-z0-9+/=]{40,}"
    rb"|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"
    rb"|\bgh[pousr]_[A-Za-z0-9]{36,}\b"
    rb"|\bgithub_pat_[A-Za-z0-9_]{40,}\b"
    rb"|\bsk_live_[A-Za-z0-9]{20,}\b"
    rb"|\bxox[baprs]-[A-Za-z0-9-]{24,}\b"
)
SECRET_MARKERS = (b"-----BEGIN", b"AKIA", b"ASIA", b"gh", b"github_pat_", b"sk_live_", b"xox")


class DistributionError(ValueError):
    """The input cannot produce the stated distribution safely."""


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inside(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def safe_name(name):
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or name.startswith("/") or name.endswith("/")
            or any(p in ("", ".", "..") for p in name.split("/"))):
        raise DistributionError("unsafe relative path: " + repr(name))
    return name


def exclusion(name):
    parts = [part.casefold() for part in PurePosixPath(name).parts]
    leaf = parts[-1]
    if any(part in DENIED_PARTS for part in parts):
        return "repository metadata, installed dependencies, or local cache"
    if (leaf in SECRET_NAMES or leaf.endswith((".pem", ".key", ".p12", ".pfx"))
            or (leaf.startswith(".env") and leaf not in ENV_TEMPLATES)):
        return "secret-bearing filename"
    if leaf.endswith((".pyc", ".pyo")):
        return "interpreter cache"
    return None


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], check=False,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise DistributionError("git inventory failed: " + " ".join(args))
    return result.stdout


def tracked_files(root):
    files = {}
    for row in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not row:
            continue
        header, path = row.split(b"\t", 1)
        mode, _, stage = header.decode("ascii").split()
        name = safe_name(path.decode("utf-8"))
        if stage != "0" or mode not in {"100644", "100755", "120000"}:
            raise DistributionError("unmerged or unsupported Git entry: " + name)
        files[name] = mode
    return files


def select_files(root, additions=()):
    tracked = tracked_files(root)
    added = {safe_name(name) for name in additions}
    excluded = []
    names = []
    for name in sorted(set(tracked) | added):
        reason = exclusion(name)
        if reason:
            if name in added:
                raise DistributionError("explicit file is excluded: " + name)
            excluded.append({"path": name, "reason": reason})
        else:
            names.append(name)
    if ARCHIVE_MANIFEST in names:
        raise DistributionError("reserved generated path: " + ARCHIVE_MANIFEST)
    return names, excluded, sorted(added - set(tracked))


def read_source(root, name, selected):
    """Read only a selected, regular file whose canonical path stays permitted."""
    safe_name(name)
    if exclusion(name):
        raise DistributionError("excluded source path: " + name)
    path = root / name
    try:
        resolved = path.resolve(strict=True)
        if not inside(resolved, root):
            raise DistributionError("symlink escapes source: " + name)
        target = resolved.relative_to(root).as_posix()
        if exclusion(target) or target not in selected:
            raise DistributionError("symlink target not in selected safe files: " + name)
        mode = path.lstat().st_mode
        if not resolved.is_file() or not (stat.S_ISREG(mode) or stat.S_ISLNK(mode)):
            raise DistributionError("not a regular file or file symlink: " + name)
        data = resolved.read_bytes()
        if any(marker in data for marker in SECRET_MARKERS) and SECRET_BYTES.search(data):
            raise DistributionError("possible credential content; inspect privately: " + name)
        record = {"path": name, "kind": "file", "mode": "0755" if mode & 0o111 else "0644",
                  "size": len(data), "sha256": digest(data)}
        if stat.S_ISLNK(mode):
            link = os.readlink(path)
            # Validate the literal target too: an absolute internal link is not portable.
            if Path(link).is_absolute() or "\\" in link or any(ord(c) < 32 for c in link):
                raise DistributionError("non-portable symlink: " + name)
            record.update(kind="symlink", mode="120000", target=link,
                          resolved_target=target, size=len(os.fsencode(link)),
                          sha256=digest(os.fsencode(link)))
        return record, data
    except (OSError, RuntimeError) as error:
        raise DistributionError("missing or unreadable source: " + name) from error


def source_snapshot(root, names):
    selected = set(names)
    return {name: read_source(root, name, selected) for name in names}


def source_records(snapshot):
    return [snapshot[name][0] for name in sorted(snapshot)]


def parse_json(snapshot, name):
    if name not in snapshot:
        raise DistributionError("required file absent from selection: " + name)
    try:
        return json.loads(snapshot[name][1])
    except (UnicodeError, ValueError) as error:
        raise DistributionError("invalid JSON: " + name) from error


def inventory(root, snapshot, date):
    """Snapshot LOCAL bytes; upstream pins remain the registry's values."""
    try:
        if datetime.date.fromisoformat(date).isoformat() != date:
            raise ValueError()
    except ValueError as error:
        raise DistributionError("snapshot date must be YYYY-MM-DD") from error
    registry = parse_json(snapshot, REGISTRY_PATH)
    entries = []
    seen = set()
    for item in registry["entries"]:
        if item["id"] in seen:
            raise DistributionError("duplicate upstream id: " + item["id"])
        seen.add(item["id"])
        files = set()
        for path in item["fabius_paths"]:
            safe_name(path)
            children = {name for name in snapshot if name == path or name.startswith(path + "/")}
            if not children:
                raise DistributionError("missing upstream local path: " + path)
            files.update(children)
            if item["consumed_as"] == "bundled":
                for required in ["LICENSE"] + (["NOTICE"] if item["notice_required"] else []):
                    if path + "/" + required not in children:
                        raise DistributionError("missing bundled attribution: " + path + "/" + required)
        records = [snapshot[name][0] for name in sorted(files)]
        entries.append({"id": item["id"], "repo": item["repo"], "license": item["license"],
                        "consumed_as": item["consumed_as"], "pinned_commit": item["pinned_commit"],
                        "pinned_version": item["pinned_version"], "pinned_at": item["pinned_at"],
                        "local_paths": item["fabius_paths"], "files": records,
                        "local_tree_sha256": digest(canonical(records))})
    return {
        "schema": "fabius-local-content/v1", "snapshot_date": date,
        "source_head": git(root, "rev-parse", "HEAD").decode().strip(),
        "registry_sha256": digest(snapshot[REGISTRY_PATH][1]),
        "meaning": "Local inventory at snapshot_date, not upstream originality, import date, or proof of an upstream revision. Null historical pins remain unknown. Symlink hashes cover their literal target bytes, not dereferenced contents.",
        "tree_hash_method": "SHA-256 of UTF-8 canonical JSON (sorted keys, compact separators, one trailing LF) of path-sorted file records.",
        "entries": sorted(entries, key=lambda entry: entry["id"]),
    }


def check_inventory(root, snapshot):
    saved = parse_json(snapshot, CONTENT_PATH)
    fresh = inventory(root, snapshot, saved["snapshot_date"])
    # The snapshot commit is historical evidence, not a mutable release version.
    for key in ("schema", "registry_sha256", "entries"):
        if saved.get(key) != fresh[key]:
            raise DistributionError("local content inventory drift: " + key + "; regenerate inventory explicitly")
    return saved


def check(root, additions=()):
    """Read-only inventory verification, suitable for a release gate."""
    root = root.resolve(strict=True)
    names, _, _ = select_files(root, additions)
    saved = check_inventory(root, source_snapshot(root, names))
    return {"status": "local content inventory matches selected source bytes",
            "snapshot_date": saved["snapshot_date"], "snapshot_source_head": saved["source_head"],
            "entry_count": len(saved["entries"]),
            "unknown_historical_pin_count": sum(entry["pinned_commit"] is None for entry in saved["entries"]),
            "local_file_count": sum(len(entry["files"]) for entry in saved["entries"]),
            "scope": "Read-only local hashes, registry equality, and bundled LICENSE/NOTICE presence; upstream originality, historical pin recovery, and host compatibility are not established."}


def markdown_targets(body):
    # Fenced examples and inline code are not resource declarations.
    lines = []
    fence = None
    for line in body.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"(`+).*?\1", "", text)
    # Inline links/images, reference definitions, and explicit HTML resources.
    # One balanced parenthesis level covers ordinary Markdown URL destinations.
    destination = r"(<[^>\n]+>|(?:[^\s()]|\([^()]*\))+?)"
    for match in re.finditer(r"\]\(\s*" + destination + r"(?:\s+[\"'][^\n]*?[\"'])?\s*\)", text):
        yield match.group(1).strip("<>")
    for match in re.finditer(r"^\s*\[[^\]\n]+\]:\s*(<[^>]+>|\S+)", text, re.M):
        yield match.group(1).strip("<>")
    for match in re.finditer(r"\b(?:src|href)\s*=\s*[\"']([^\"']+)[\"']", text):
        yield match.group(1)


def link_target(source, raw):
    try:
        url = urlsplit(raw)
    except ValueError as error:
        raise DistributionError("invalid resource link in " + source) from error
    if url.scheme or url.netloc or not url.path:
        return None
    path = unquote(url.path)
    if path.startswith("/"):
        raise DistributionError("absolute local resource link in " + source + ": " + raw)
    target = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
    safe_name(target)
    return target


def check_closure(snapshot, registry):
    names = set(snapshot)
    directories = {parent.as_posix() for name in names for parent in PurePosixPath(name).parents}
    # Full reference corpora are data. Their historical examples are preserved,
    # and broken links are reported, never silently counted as satisfied.
    vendor_roots = [path for item in registry["entries"] if item["consumed_as"] == "bundled"
                    for path in item["fabius_paths"]]
    # These preserved reference libraries predate the upstream registry's scope.
    vendor_roots += ["skills/fabius-cohors/references/agents", "skills/fabius-decor/references/design",
                     "skills/fabius-disciplina/references/process", "skills/fabius-parcus/references/lean",
                     "skills/fabius-archivum/references/knowledge"]
    missing_vendor = []
    checked = 0
    failures = []
    for name, (_, data) in snapshot.items():
        if not name.endswith(".md"):
            continue
        vendor = any(name.startswith(path + "/") for path in vendor_roots)
        for raw in markdown_targets(data.decode("utf-8")):
            try:
                target = link_target(name, raw)
                if target is None:
                    continue
                if target in names or target in directories:
                    checked += 1
                    continue
                issue = {"source": name, "link": raw, "target": target}
            except DistributionError:
                if not vendor:
                    raise
                issue = {"source": name, "link": raw, "target": None}
            if vendor:
                missing_vendor.append(issue)
            else:
                failures.append(issue)
    if failures:
        raise DistributionError("missing authored local resource(s): " + json.dumps(failures, ensure_ascii=False))
    return {"checked_local_links": checked,
            "scope": "Markdown inline/reference links and HTML src/href outside fenced/inline examples. Authored missing targets fail; preserved reference corpora gaps are explicitly listed. Language imports, generated target-project examples, remote URLs, and fragment anchors are not proven by this check.",
            "preserved_reference_roots": sorted(set(vendor_roots)),
            "unresolved_reference_links": sorted(missing_vendor, key=lambda row: (row["source"], row["link"]))}


def validate_plugin(snapshot):
    plugin = parse_json(snapshot, ".claude-plugin/plugin.json")
    if not isinstance(plugin.get("description"), str) or not plugin["description"].strip():
        raise DistributionError("plugin description is required")
    skills = sorted(path for path in snapshot if re.fullmatch(r"skills/[^/]+/SKILL\.md", path))
    declared = sorted(safe_name(path.removeprefix("./")) + "/SKILL.md" for path in plugin["skills"])
    if len(skills) != 15 or declared != skills:
        raise DistributionError("plugin must declare exactly its fifteen root SKILL.md files")
    nested = [path for path in snapshot if path.endswith("/SKILL.md") and path not in skills]
    if nested:
        raise DistributionError("nested discoverable skill: " + nested[0])
    for name in ("LICENSE", "NOTICE", "credits/README.md", REGISTRY_PATH, CONTENT_PATH):
        if name not in snapshot:
            raise DistributionError("required attribution/manifest absent: " + name)
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?", plugin.get("version", "")):
        raise DistributionError("invalid distribution version")
    return plugin, skills


def outside_git(output, source):
    output = output.resolve()
    if inside(output, source):
        raise DistributionError("output directory must be outside the source checkout")
    if any((parent / ".git").exists() for parent in [output, *output.parents]):
        raise DistributionError("output directory must be outside any Git checkout")
    return output


def write_zip(path, payload):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for name, (mode, data) in sorted(payload.items()):
            info = zipfile.ZipInfo(safe_name(name), ZIP_DATE)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | int(mode, 8)) << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, data)


def build(root, output, additions=()):
    root = root.resolve(strict=True)
    output = outside_git(output, root)
    head = git(root, "rev-parse", "HEAD").decode().strip()
    names, excluded, added = select_files(root, additions)
    snapshot = source_snapshot(root, names)
    plugin, skills = validate_plugin(snapshot)
    saved_inventory = check_inventory(root, snapshot)
    closure = check_closure(snapshot, parse_json(snapshot, REGISTRY_PATH))
    records = source_records(snapshot)
    scope_hash = digest(canonical(records))
    changed = {safe_name(path) for path in git(root, "diff", "HEAD", "--name-only", "-z").decode().split("\0") if path}
    changed = sorted({path for path in changed if not exclusion(path)} | set(added))
    payload = {}
    files = []
    for name, (record, data) in snapshot.items():
        mode = "0644" if record["kind"] == "symlink" else record["mode"]
        payload[name] = (mode, data)
        files.append({"path": name, "size": len(data), "sha256": digest(data), "mode": mode})
    manifest = {
        "schema": "fabius-distribution/v1", "format": "claude-compatible-plugin-zip",
        "status": "direct-import candidate; not store-approved or deployment-verified",
        "version": plugin["version"], "source_head": head,
        "source_scope": "Git tracked paths plus explicitly named release-owned files, minus listed exclusions. Unselected untracked/ignored files are not hashed. Source bytes and modes are snapshotted; symlink source hashes cover link text. This hash is not a signature or upstream provenance proof.",
        "source_scope_sha256": scope_hash, "dirty_source": bool(changed),
        "dirty_source_paths": changed, "dirty_source_byte_sha256": scope_hash if changed else None,
        "removed_tracked_paths": sorted(set(changed) - set(names)),
        "explicit_untracked_files": added, "excluded_tracked_files": excluded,
        "source_files": records, "files": files,
        "source_file_count": len(files), "archive_entry_count": len(files) + 1,
        "root_skills": skills,
        "quarantined_reference_count": sum(name.endswith("/REFERENCE.md") for name in names),
        "runtime_included": any(name.startswith("runtime/") for name in names),
        "content_inventory_snapshot_date": saved_inventory["snapshot_date"],
        "upstream_entry_count": len(saved_inventory["entries"]),
        "unknown_historical_pin_count": sum(entry["pinned_commit"] is None for entry in saved_inventory["entries"]),
        "symlink_policy": "Safe internal file symlinks are materialized as regular files; source link text and resolved target are recorded in source_files. Directory, escaping, excluded, missing, and unselected targets fail.",
        "zip_metadata": "Path-sorted ZIP_STORED entries; UTC-independent 1980-01-01 timestamp; Unix regular-file modes 0644/0755; no host paths, build clock, UID/GID, or ZIP comment. Stored compression avoids zlib-version variation.",
        "resource_closure": closure,
        "limitations": [
            "Preserved vendored source is reference data, not executed, installed, or certified runnable; unresolved historical links are listed.",
            "Filename exclusions and high-confidence credential patterns are safeguards, not a complete secret audit. Use the repository's release secret gate before publication.",
            "Native Codex sparse caches previously omitted root credits/development paths and a symlink; this complete ZIP does not prove that a native cache contains them.",
            "Claude-compatible archive root is retained for direct import. Actual portal conversion, scanning, acceptance, installation, and a fresh host task are pending; no invented ChatGPT or Codex export schema is emitted.",
            "The archive includes existing provenance evidence as data; it is not a newly signed or approved release. Verify release authority separately.",
        ],
    }
    payload[ARCHIVE_MANIFEST] = ("0644", canonical(manifest))
    # Avoid a mixed snapshot when other agents are editing the same checkout.
    if (head != git(root, "rev-parse", "HEAD").decode().strip()
            or select_files(root, additions)[0] != names
            or source_records(source_snapshot(root, names)) != records):
        raise DistributionError("source changed during build; retry after edits settle")
    output.mkdir(parents=True, exist_ok=True)
    target = output / ("fabius-" + plugin["version"] + "-claude-plugin.zip")
    if target.exists() or target.is_symlink():
        raise DistributionError("archive already exists; select a new output directory")
    fd, temporary = tempfile.mkstemp(prefix=".fabius-distribution-", suffix=".zip", dir=output)
    os.close(fd)
    try:
        write_zip(temporary, payload)
        receipt = verify(Path(temporary))
        # Link publishes without overwriting another process's archive.
        os.link(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    receipt["archive"] = str(target)
    return receipt


def verify(path, expected_sha256=None):
    """Verify content integrity without extraction or trusting embedded commands."""
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise DistributionError("archive exceeds size limit")
    data_hash = digest(path.read_bytes())
    if expected_sha256 is not None and data_hash != expected_sha256:
        raise DistributionError("archive SHA-256 does not match expected value")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [safe_name(info.filename) for info in infos]
        if (names != sorted(names) or len(names) != len(set(unicodedata.normalize("NFC", name).casefold() for name in names))
                or len(names) > 50000 or sum(info.file_size for info in infos) > MAX_ARCHIVE_BYTES):
            raise DistributionError("archive ordering, duplicate paths, or size limit invalid")
        for info in infos:
            mode = info.external_attr >> 16
            if (exclusion(info.filename) or info.date_time != ZIP_DATE
                    or info.compress_type != zipfile.ZIP_STORED or info.flag_bits & 1 or not stat.S_ISREG(mode)
                    or stat.S_IMODE(mode) not in (0o644, 0o755)):
                raise DistributionError("unsafe/noncanonical archive entry: " + info.filename)
        manifest = json.loads(archive.read(ARCHIVE_MANIFEST))
        if manifest.get("schema") != "fabius-distribution/v1":
            raise DistributionError("unsupported distribution manifest")
        declared = manifest["files"]
        if (sorted(row["path"] for row in declared) != [name for name in names if name != ARCHIVE_MANIFEST]
                or manifest["archive_entry_count"] != len(names)
                or manifest["source_file_count"] != len(declared)):
            raise DistributionError("archive manifest membership mismatch")
        for row in declared:
            body = archive.read(row["path"])
            if digest(body) != row["sha256"] or len(body) != row["size"]:
                raise DistributionError("archive file hash mismatch: " + row["path"])
            if format(stat.S_IMODE(archive.getinfo(row["path"]).external_attr >> 16), "04o") != row["mode"]:
                raise DistributionError("archive file mode mismatch: " + row["path"])
        if digest(canonical(manifest["source_files"])) != manifest["source_scope_sha256"]:
            raise DistributionError("source scope hash mismatch")
    return {"archive": str(path.resolve()), "sha256": data_hash, "size_bytes": path.stat().st_size,
            "source_head": manifest["source_head"], "source_scope_sha256": manifest["source_scope_sha256"],
            "dirty_source": manifest["dirty_source"], "file_count": len(declared), "archive_entry_count": len(names),
            "root_skill_count": len(manifest["root_skills"]),
            "quarantined_reference_count": manifest["quarantined_reference_count"],
            "upstream_entry_count": manifest["upstream_entry_count"],
            "unknown_historical_pin_count": manifest["unknown_historical_pin_count"],
            "unresolved_reference_link_count": len(manifest["resource_closure"]["unresolved_reference_links"]),
            "status": manifest["status"], "verification": "internal hashes checked; authenticity and host import not established"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "inventory", "check"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--source", type=Path, default=Path(__file__).resolve().parent.parent)
        sub.add_argument("--include-file", action="append", default=[], help="Exact release-owned path to include even if untracked; repeat as needed")
        if command == "build":
            sub.add_argument("--output-dir", type=Path, required=True, help="User-selected directory outside any Git checkout")
        elif command == "inventory":
            sub.add_argument("--snapshot-date", required=True, help="Explicit local-inventory date, YYYY-MM-DD")
    sub = subparsers.add_parser("verify")
    sub.add_argument("archive", type=Path)
    sub.add_argument("--expected-sha256")
    args = parser.parse_args()
    try:
        if args.command == "build":
            result = build(args.source, args.output_dir, args.include_file)
        elif args.command == "verify":
            result = verify(args.archive, args.expected_sha256)
        elif args.command == "check":
            result = check(args.source, args.include_file)
        else:
            root = args.source.resolve(strict=True)
            names, _, _ = select_files(root, args.include_file)
            # This command owns only the explicitly requested generated inventory.
            snapshot = source_snapshot(root, [name for name in names if name != CONTENT_PATH])
            result = inventory(root, snapshot, args.snapshot_date)
            target = root / CONTENT_PATH
            if target.is_symlink() or not inside(target.parent.resolve(), root):
                raise DistributionError("inventory target must remain inside source")
            target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            result = {"path": str(target), "entry_count": len(result["entries"]),
                      "unknown_historical_pin_count": sum(e["pinned_commit"] is None for e in result["entries"]),
                      "meaning": result["meaning"]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (DistributionError, OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, "distribution: " + str(error) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())

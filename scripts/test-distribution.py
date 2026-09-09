#!/usr/bin/env python3
"""Adversarial filesystem/ZIP tests; no vendored code or network is executed."""

import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile


spec = importlib.util.spec_from_file_location("distribution", Path(__file__).with_name("distribution.py"))
distribution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(distribution)


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="fabius-distribution-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "source"
        self.root.mkdir()
        self.tracked = set()
        self.changed = set()
        self.patcher = patch.object(distribution, "git", self.git_inventory)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        skills = ["./skills/skill-" + str(i) for i in range(15)]
        self.put(".claude-plugin/plugin.json", json.dumps({"name": "fixture", "version": "1.0.0",
                  "description": "Synthetic distribution test fixture", "skills": skills}))
        for path in skills:
            self.put(path.removeprefix("./") + "/SKILL.md", "# Fixture contract\n")
        self.put("LICENSE", "Fixture license\n")
        self.put("NOTICE", "Fixture notice\n")
        self.put("credits/README.md", "Fixture credits\n")
        self.put("README.md", "[Start](skills/skill-0/SKILL.md)\n")
        self.vendor = "skills/skill-1/references/vendor"
        self.put(self.vendor + "/REFERENCE.md", "# Preserved fixture\n")
        self.put(self.vendor + "/LICENSE", "Fixture license\n")
        self.put(self.vendor + "/NOTICE", "Fixture notice\n")
        self.put("skills/skill-0/references/original.md", "# Original reference\n")
        self.put("credits/upstream.json", json.dumps({"entries": [
            {"id": "legacy", "repo": "https://example.invalid/legacy", "license": "Apache-2.0",
             "consumed_as": "bundled", "fabius_paths": [self.vendor], "pinned_commit": None,
             "pinned_version": None, "pinned_at": None, "notice_required": True},
            {"id": "known", "repo": "https://example.invalid/known", "license": "MIT",
             "consumed_as": "informed-by", "fabius_paths": ["skills/skill-0/references/original.md"],
             "pinned_commit": "a" * 40, "pinned_version": None, "pinned_at": "2026-09-08",
             "notice_required": False},
        ]}))
        self.refresh_inventory()

    def git_inventory(self, root, *args):
        self.assertEqual(root, self.root)
        if args == ("rev-parse", "HEAD"):
            return ("b" * 40 + "\n").encode()
        if args == ("ls-files", "--stage", "-z"):
            return b"".join(("100644 " + "c" * 40 + " 0\t" + path + "\0").encode()
                            for path in sorted(self.tracked))
        if args == ("diff", "HEAD", "--name-only", "-z"):
            return "\0".join(sorted(self.changed)).encode()
        self.fail("unexpected Git operation: " + repr(args))

    def put(self, name, text, tracked=True):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        if tracked:
            self.tracked.add(name)
        return path

    def refresh_inventory(self):
        names, _, _ = distribution.select_files(self.root)
        snapshot = distribution.source_snapshot(self.root, [p for p in names if p != distribution.CONTENT_PATH])
        content = distribution.inventory(self.root, snapshot, "2026-09-09")
        self.put(distribution.CONTENT_PATH, json.dumps(content))

    def build(self, directory="output", additions=()):
        return distribution.build(self.root, self.base / directory, additions)

    def test_two_builds_are_byte_identical(self):
        first = self.build("one")
        second = self.build("two")
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(Path(first["archive"]).read_bytes(), Path(second["archive"]).read_bytes())
        self.assertEqual(first["root_skill_count"], 15)
        self.assertFalse(first["dirty_source"])

    def test_missing_authored_local_link_fails(self):
        self.put("README.md", "[Required](missing.md)\n")
        with self.assertRaisesRegex(distribution.DistributionError, "missing authored local"):
            self.build()

    def test_cross_skill_and_root_credit_links_resolve(self):
        self.put("skills/skill-0/SKILL.md", "[Peer](../skill-1/SKILL.md)\n[Credits](../../credits/README.md)\n")
        self.build()

    def test_reference_definitions_and_html_assets_are_checked(self):
        for body in ('[asset]: missing.png\n', '<img src="missing.png">\n'):
            self.put("README.md", body)
            with self.assertRaisesRegex(distribution.DistributionError, "missing authored local"):
                self.build()

    def test_fenced_examples_and_remote_badges_are_not_local_paths(self):
        self.put("README.md", '```md\n[Example](not-a-file.md)\n```\n'
                 '[![Badge](https://example.invalid/a.svg)](https://example.invalid/)\n')
        self.build()

    def test_preserved_vendor_gap_is_reported_not_fixed(self):
        self.put(self.vendor + "/REFERENCE.md", "[Historical example](old-unbundled.md)\n")
        self.refresh_inventory()
        result = self.build()
        self.assertEqual(result["unresolved_reference_link_count"], 1)
        self.assertIn("old-unbundled.md", (self.root / self.vendor / "REFERENCE.md").read_text())

    def test_inventory_drift_blocks_distribution(self):
        self.put(self.vendor + "/REFERENCE.md", "Changed source after local inventory\n")
        with self.assertRaisesRegex(distribution.DistributionError, "inventory drift"):
            self.build()

    def test_inventory_preserves_unknown_pins(self):
        content = json.loads((self.root / distribution.CONTENT_PATH).read_text())
        entries = {e["id"]: e for e in content["entries"]}
        self.assertIsNone(entries["legacy"]["pinned_commit"])
        self.assertIsNone(entries["legacy"]["pinned_at"])
        self.assertEqual(entries["known"]["pinned_commit"], "a" * 40)
        self.assertIn("not upstream originality", content["meaning"])

    def test_inventory_check_is_read_only_and_detects_drift(self):
        before = (self.root / distribution.CONTENT_PATH).read_bytes()
        result = distribution.check(self.root)
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["unknown_historical_pin_count"], 1)
        self.assertEqual((self.root / distribution.CONTENT_PATH).read_bytes(), before)
        self.put(self.vendor + "/REFERENCE.md", "Unexpected change\n")
        with self.assertRaisesRegex(distribution.DistributionError, "inventory drift"):
            distribution.check(self.root)
        self.assertEqual((self.root / distribution.CONTENT_PATH).read_bytes(), before)

    def test_missing_license_blocks_inventory(self):
        path = self.vendor + "/LICENSE"
        self.tracked.remove(path)
        (self.root / path).unlink()
        with self.assertRaisesRegex(distribution.DistributionError, "missing bundled attribution"):
            self.refresh_inventory()

    def test_untracked_file_requires_explicit_selection(self):
        self.put("scratch.txt", "must not ship\n", tracked=False)
        result = self.build()
        with zipfile.ZipFile(result["archive"]) as archive:
            self.assertNotIn("scratch.txt", archive.namelist())
        result = self.build("selected", ["scratch.txt"])
        self.assertTrue(result["dirty_source"])
        with zipfile.ZipFile(result["archive"]) as archive:
            self.assertEqual(archive.read("scratch.txt"), b"must not ship\n")

    def test_dirty_source_changes_hash(self):
        first = self.build("one")
        self.put("README.md", "A changed authored document.\n")
        self.changed.add("README.md")
        second = self.build("two")
        self.assertNotEqual(first["source_scope_sha256"], second["source_scope_sha256"])
        self.assertTrue(second["dirty_source"])

    def test_staged_deletion_marks_selected_source_dirty(self):
        self.put("extra-document.md", "Originally tracked\n")
        self.tracked.remove("extra-document.md")
        (self.root / "extra-document.md").unlink()
        self.changed.add("extra-document.md")
        result = self.build()
        self.assertTrue(result["dirty_source"])
        with zipfile.ZipFile(result["archive"]) as archive:
            manifest = json.loads(archive.read(distribution.ARCHIVE_MANIFEST))
            self.assertIn("extra-document.md", manifest["removed_tracked_paths"])

    def test_concurrent_source_change_prevents_publication(self):
        original = distribution.source_snapshot
        calls = 0

        def changed_snapshot(root, names):
            nonlocal calls
            calls += 1
            if calls == 2:
                self.put("README.md", "Concurrent edit\n")
            return original(root, names)

        with patch.object(distribution, "source_snapshot", changed_snapshot):
            with self.assertRaisesRegex(distribution.DistributionError, "source changed during build"):
                self.build()
        self.assertFalse((self.base / "output").exists())

    def test_missing_tracked_source_prevents_publication(self):
        (self.root / "NOTICE").unlink()
        with self.assertRaisesRegex(distribution.DistributionError, "missing or unreadable source"):
            self.build()

    def test_excluded_files_never_ship_and_explicit_selection_fails(self):
        for name in (".env", ".git/config", ".venv/module.py", "node_modules/x.js", ".cache/x", "private.key"):
            self.put(name, "sensitive fixture\n")
        result = self.build()
        with zipfile.ZipFile(result["archive"]) as archive:
            self.assertFalse(any(distribution.exclusion(p) for p in archive.namelist()))
        with self.assertRaisesRegex(distribution.DistributionError, "explicit file is excluded"):
            self.build("explicit", [".env"])

    def test_credential_content_fails_without_echoing_secret(self):
        token = "sk_" + "live_" + "A" * 24
        self.put("accident.txt", token)
        with self.assertRaises(distribution.DistributionError) as caught:
            self.build()
        self.assertIn("possible credential", str(caught.exception))
        self.assertNotIn(token, str(caught.exception))

    def test_safe_symlink_is_materialized_and_source_link_recorded(self):
        (self.root / "alias.md").symlink_to("README.md")
        self.tracked.add("alias.md")
        result = self.build()
        with zipfile.ZipFile(result["archive"]) as archive:
            info = archive.getinfo("alias.md")
            self.assertTrue(stat.S_ISREG(info.external_attr >> 16))
            self.assertEqual(archive.read("alias.md"), archive.read("README.md"))
            manifest = json.loads(archive.read(distribution.ARCHIVE_MANIFEST))
            record = next(r for r in manifest["source_files"] if r["path"] == "alias.md")
            self.assertEqual(record["kind"], "symlink")
            self.assertEqual(record["target"], "README.md")

    def test_escaping_and_unselected_symlink_targets_fail(self):
        outside = self.base / "outside.txt"
        outside.write_text("must never be included\n")
        link = self.root / "alias.md"
        self.tracked.add("alias.md")
        link.symlink_to("../outside.txt")
        with self.assertRaisesRegex(distribution.DistributionError, "symlink escapes"):
            self.build()
        link.unlink()
        self.put("unselected.md", "not selected\n", tracked=False)
        link.symlink_to("unselected.md")
        with self.assertRaisesRegex(distribution.DistributionError, "not in selected safe files"):
            self.build()

    def test_directory_symlink_escape_fails(self):
        (self.root / "redirect").symlink_to(self.base, target_is_directory=True)
        (self.base / "outside.txt").write_text("outside\n")
        self.tracked.add("redirect/outside.txt")
        with self.assertRaisesRegex(distribution.DistributionError, "symlink escapes"):
            self.build()

    def test_unsafe_selection_and_resource_paths_fail(self):
        for name in ("../outside", "/absolute", "x\\y", "x/../y", "x//y", "C:/x", "bad\nname"):
            with self.subTest(name=name), self.assertRaises(distribution.DistributionError):
                distribution.select_files(self.root, [name])
        self.put("README.md", "[Escape](%2e%2e/outside.txt)\n")
        with self.assertRaises(distribution.DistributionError):
            self.build()

    def test_nested_discoverable_skill_fails(self):
        self.put(self.vendor + "/SKILL.md", "Accidental public contract\n")
        with self.assertRaisesRegex(distribution.DistributionError, "nested discoverable skill"):
            self.build()

    def test_inside_checkout_output_and_overwrite_fail(self):
        with self.assertRaisesRegex(distribution.DistributionError, "outside the source"):
            distribution.build(self.root, self.root / "outputs")
        first = self.build()
        original = Path(first["archive"]).read_bytes()
        with self.assertRaisesRegex(distribution.DistributionError, "already exists"):
            self.build()
        self.assertEqual(Path(first["archive"]).read_bytes(), original)

    def test_tampering_and_removal_fail_verification(self):
        result = self.build()
        with zipfile.ZipFile(result["archive"]) as archive:
            original = {info.filename: (format(stat.S_IMODE(info.external_attr >> 16), "04o"),
                        archive.read(info.filename)) for info in archive.infolist()}
        for name, mutate, message in (
            ("tamper.zip", lambda p: p.update({"README.md": ("0644", b"changed")}), "hash mismatch"),
            ("remove.zip", lambda p: p.pop("README.md"), "membership mismatch"),
        ):
            payload = dict(original)
            mutate(payload)
            target = self.base / name
            distribution.write_zip(target, payload)
            with self.assertRaisesRegex(distribution.DistributionError, message):
                distribution.verify(target)
        with self.assertRaisesRegex(distribution.DistributionError, "SHA-256"):
            distribution.verify(Path(result["archive"]), "0" * 64)

    def test_unsafe_archive_entry_fails_before_extraction(self):
        target = self.base / "traversal.zip"
        with zipfile.ZipFile(target, "w") as archive:
            archive.writestr("../escaped.txt", "outside")
        with self.assertRaisesRegex(distribution.DistributionError, "unsafe relative path"):
            distribution.verify(target)
        self.assertFalse((self.base / "escaped.txt").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

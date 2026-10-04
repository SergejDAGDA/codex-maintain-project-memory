import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "maintain-project-memory" / "scripts" / "check_skill_freshness.py"
SPEC = importlib.util.spec_from_file_location("check_skill_freshness", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SkillFreshnessTests(unittest.TestCase):
    def test_git_blob_sha_matches_known_empty_blob(self) -> None:
        self.assertEqual(
            MODULE.git_blob_sha(b""),
            "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
        )

    def test_local_blob_map_ignores_python_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text("hello\n", encoding="utf-8")
            cache = root / "scripts" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "x.pyc").write_bytes(b"cache")
            result = MODULE.local_blob_map(root)
            self.assertEqual(set(result), {"SKILL.md"})

    def test_payload_digest_is_stable_for_map_order(self) -> None:
        first = {"b": "2", "a": "1"}
        second = {"a": "1", "b": "2"}
        self.assertEqual(MODULE.payload_digest(first), MODULE.payload_digest(second))

    def test_compare_blob_maps_reports_all_difference_types(self) -> None:
        local = {"same": "1", "changed": "old", "extra": "x"}
        remote = {"same": "1", "changed": "new", "missing": "m"}
        missing, extra, mismatched = MODULE.compare_blob_maps(local, remote)
        self.assertEqual(missing, ("missing",))
        self.assertEqual(extra, ("extra",))
        self.assertEqual(mismatched, ("changed",))

    def test_exact_maps_have_no_differences(self) -> None:
        sample = {"SKILL.md": "abc", "scripts/x.py": "def"}
        self.assertEqual(MODULE.compare_blob_maps(sample, dict(sample)), ((), (), ()))

    def test_canonical_blob_map_reports_commit_and_filters_skill_subtree(self) -> None:
        branch = {
            "commit": {
                "sha": "commit123",
                "commit": {"tree": {"sha": "tree123"}},
            }
        }
        tree = {
            "truncated": False,
            "tree": [
                {
                    "path": "skills/maintain-project-memory/SKILL.md",
                    "type": "blob",
                    "sha": "blob-skill",
                },
                {
                    "path": "skills/maintain-project-memory/scripts/__pycache__/x.pyc",
                    "type": "blob",
                    "sha": "blob-cache",
                },
                {
                    "path": "README.md",
                    "type": "blob",
                    "sha": "blob-readme",
                },
            ],
        }
        with mock.patch.object(MODULE, "_request_json", side_effect=[branch, tree]):
            commit, files = MODULE.canonical_blob_map(timeout=1.0)
        self.assertEqual(commit, "commit123")
        self.assertEqual(files, {"SKILL.md": "blob-skill"})

    def _write_receipt(self, root: Path, receipt_path: Path, commit: str) -> None:
        blobs = MODULE.local_blob_map(root)
        receipt_path.write_text(
            json.dumps(
                {
                    "schema": MODULE.PROVENANCE_SCHEMA,
                    "canonical_repository": f"https://github.com/{MODULE.CANONICAL_REPOSITORY}",
                    "canonical_branch": MODULE.CANONICAL_BRANCH,
                    "canonical_commit": commit,
                    "payload_digest": MODULE.payload_digest(blobs),
                    "recorded_at_utc": "2026-10-04T12:00:00Z",
                }
            ),
            encoding="utf-8",
        )

    def test_offline_receipt_with_expected_commit_is_write_eligible(self) -> None:
        commit = "a" * 40
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            root.mkdir()
            (root / "SKILL.md").write_text("hello\n", encoding="utf-8")
            receipt = Path(tmp) / "receipt.json"
            self._write_receipt(root, receipt, commit)

            result = MODULE.local_provenance_result(
                root,
                receipt,
                commit,
                urllib.error.URLError("blocked"),
            )

        self.assertEqual(result["status"], "verified-local")
        self.assertTrue(result["provenance_payload_match"])
        self.assertTrue(result["expected_commit_match"])
        self.assertTrue(result["write_eligible"])
        self.assertEqual(result["canonical_currentness"], "unverified-offline")

    def test_offline_receipt_without_expected_commit_is_read_only(self) -> None:
        commit = "b" * 40
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            root.mkdir()
            (root / "SKILL.md").write_text("hello\n", encoding="utf-8")
            receipt = Path(tmp) / "receipt.json"
            self._write_receipt(root, receipt, commit)

            result = MODULE.local_provenance_result(
                root,
                receipt,
                None,
                urllib.error.URLError("blocked"),
            )

        self.assertEqual(result["status"], "verified-local")
        self.assertIsNone(result["expected_commit_match"])
        self.assertFalse(result["write_eligible"])

    def test_offline_receipt_detects_payload_change(self) -> None:
        commit = "c" * 40
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            root.mkdir()
            target = root / "SKILL.md"
            target.write_text("hello\n", encoding="utf-8")
            receipt = Path(tmp) / "receipt.json"
            self._write_receipt(root, receipt, commit)
            target.write_text("changed\n", encoding="utf-8")

            result = MODULE.local_provenance_result(
                root,
                receipt,
                commit,
                urllib.error.URLError("blocked"),
            )

        self.assertEqual(result["status"], "different")
        self.assertFalse(result["provenance_payload_match"])
        self.assertFalse(result["write_eligible"])

    def test_result_payload_falls_back_to_receipt_when_online_check_is_blocked(self) -> None:
        commit = "d" * 40
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            root.mkdir()
            (root / "SKILL.md").write_text("hello\n", encoding="utf-8")
            receipt = Path(tmp) / "receipt.json"
            self._write_receipt(root, receipt, commit)

            with mock.patch.object(
                MODULE,
                "online_result",
                side_effect=urllib.error.URLError("blocked"),
            ):
                result = MODULE.result_payload(root, 1.0, receipt, commit)

        self.assertEqual(result["status"], "verified-local")
        self.assertEqual(result["verification_scope"], "recorded-install")
        self.assertTrue(result["write_eligible"])


if __name__ == "__main__":
    unittest.main()

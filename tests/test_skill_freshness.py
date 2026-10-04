import importlib.util
from pathlib import Path
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()

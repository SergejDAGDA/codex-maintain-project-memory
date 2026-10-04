import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "maintain-project-memory" / "scripts"
CHECKER = SCRIPT_DIR / "check_skill_freshness.py"
RECORDER = SCRIPT_DIR / "record_skill_provenance.py"

CHECK_SPEC = importlib.util.spec_from_file_location("check_skill_freshness", CHECKER)
CHECK_MODULE = importlib.util.module_from_spec(CHECK_SPEC)
assert CHECK_SPEC.loader is not None
CHECK_SPEC.loader.exec_module(CHECK_MODULE)
sys.modules["check_skill_freshness"] = CHECK_MODULE

REC_SPEC = importlib.util.spec_from_file_location("record_skill_provenance", RECORDER)
REC_MODULE = importlib.util.module_from_spec(REC_SPEC)
assert REC_SPEC.loader is not None
REC_SPEC.loader.exec_module(REC_MODULE)


class SkillProvenanceTests(unittest.TestCase):
    def test_build_receipt_records_commit_and_payload_digest(self) -> None:
        commit = "e" * 40
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skill"
            root.mkdir()
            (root / "SKILL.md").write_text("hello\n", encoding="utf-8")
            receipt = REC_MODULE.build_receipt(root, commit)
            blobs = CHECK_MODULE.local_blob_map(root)

        self.assertEqual(receipt["schema"], CHECK_MODULE.PROVENANCE_SCHEMA)
        self.assertEqual(receipt["canonical_commit"], commit)
        self.assertEqual(receipt["recorded_from"], "user-confirmed-install")
        self.assertEqual(receipt["payload_file_count"], 1)
        self.assertEqual(receipt["payload_digest"], CHECK_MODULE.payload_digest(blobs))

    def test_write_receipt_creates_external_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "receipt.json"
            receipt = {"schema": "x", "value": 1}
            REC_MODULE.write_receipt(path, receipt)
            loaded = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(loaded, receipt)


if __name__ == "__main__":
    unittest.main()

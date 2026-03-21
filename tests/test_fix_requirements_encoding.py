import tempfile
import unittest
from pathlib import Path

from fix_requirements_encoding import normalize_requirements_file


class FixRequirementsEncodingTests(unittest.TestCase):
    def test_normalize_requirements_file_rewrites_utf16_with_null_bytes(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            req = Path(tmp_dir) / "requirements.txt"
            req.write_bytes("fastapi==0.120.3\nuvicorn==0.38.0\n".encode("utf-16"))

            changed = normalize_requirements_file(req)

            self.assertTrue(changed)
            self.assertEqual(
                req.read_text(encoding="utf-8"),
                "fastapi==0.120.3\nuvicorn==0.38.0\n",
            )

    def test_normalize_requirements_file_leaves_clean_utf8_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            req = Path(tmp_dir) / "requirements.txt"
            req.write_text("fastapi==0.120.3\n", encoding="utf-8")

            changed = normalize_requirements_file(req)

            self.assertFalse(changed)
            self.assertEqual(req.read_text(encoding="utf-8"), "fastapi==0.120.3\n")


if __name__ == "__main__":
    unittest.main()

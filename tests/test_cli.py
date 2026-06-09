import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from knot.cli import EXIT_CYCLES_FOUND, EXIT_ERROR, EXIT_OK, main


def write_project(root: Path, files: dict) -> None:
    for rel, body in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")


def run(argv):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = main(argv)
    return code, buffer.getvalue()


class CliTests(unittest.TestCase):
    def test_clean_project_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(Path(tmp), {"a.py": "import b\n", "b.py": ""})
            code, out = run([tmp])
            self.assertEqual(code, EXIT_OK)
            self.assertIn("No circular imports", out)

    def test_cyclic_project_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(Path(tmp), {
                "pkg/__init__.py": "",
                "pkg/a.py": "from pkg import b\n",
                "pkg/b.py": "from pkg import a\n",
            })
            code, out = run([tmp])
            self.assertEqual(code, EXIT_CYCLES_FOUND)
            self.assertIn("import cycle", out)

    def test_no_fail_flag_forces_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(Path(tmp), {
                "pkg/__init__.py": "",
                "pkg/a.py": "from pkg import b\n",
                "pkg/b.py": "from pkg import a\n",
            })
            code, _ = run([tmp, "--no-fail"])
            self.assertEqual(code, EXIT_OK)

    def test_json_output_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(Path(tmp), {
                "pkg/__init__.py": "",
                "pkg/a.py": "from pkg import b\n",
                "pkg/b.py": "from pkg import a\n",
            })
            code, out = run([tmp, "--format", "json"])
            data = json.loads(out)
            self.assertEqual(data["summary"]["cycles"], 1)
            self.assertEqual(code, EXIT_CYCLES_FOUND)

    def test_mermaid_output_has_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_project(Path(tmp), {"a.py": "import b\n", "b.py": ""})
            _, out = run([tmp, "--format", "mermaid"])
            self.assertTrue(out.lstrip().startswith("graph LR"))

    def test_missing_path_errors(self):
        code, _ = run(["/no/such/path/exists/knot"])
        self.assertEqual(code, EXIT_ERROR)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from knot.analyzer import build_graph, discover_modules


def write_project(root: Path, files: dict) -> None:
    """Create a fake project tree. Keys are relative paths, values file bodies."""
    for rel, body in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")


class DiscoverModulesTests(unittest.TestCase):
    def test_package_dir_uses_dir_name_as_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "mypkg"
            write_project(root, {
                "__init__.py": "",
                "core.py": "",
                "sub/__init__.py": "",
                "sub/mod.py": "",
            })
            modules = discover_modules(root)
            self.assertEqual(
                set(modules),
                {"mypkg", "mypkg.core", "mypkg.sub", "mypkg.sub.mod"},
            )
            self.assertTrue(modules["mypkg"].is_package)
            self.assertFalse(modules["mypkg.core"].is_package)

    def test_plain_project_dir_has_no_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, {"a.py": "", "pkg/__init__.py": "", "pkg/b.py": ""})
            modules = discover_modules(root)
            self.assertEqual(set(modules), {"a", "pkg", "pkg.b"})

    def test_excludes_default_and_custom_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, {
                "a.py": "",
                ".venv/lib.py": "",
                "vendor/c.py": "",
            })
            modules = discover_modules(root, excludes=["vendor"])
            self.assertEqual(set(modules), {"a"})


class BuildGraphTests(unittest.TestCase):
    def test_resolves_absolute_imports_between_internal_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, {
                "app.py": "import helpers\nimport os\n",
                "helpers.py": "import json\n",
            })
            graph = build_graph(root)
            self.assertEqual(graph.edges["app"], {"helpers"})
            self.assertEqual(graph.edges["helpers"], set())
            # external imports recorded as unresolved, not as edges
            self.assertIn("os", graph.unresolved.get("app", set()))

    def test_resolves_from_imports_to_submodule(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, {
                "pkg/__init__.py": "",
                "pkg/a.py": "from pkg import b\n",
                "pkg/b.py": "",
            })
            graph = build_graph(root)
            self.assertEqual(graph.edges["pkg.a"], {"pkg.b"})

    def test_resolves_relative_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, {
                "pkg/__init__.py": "",
                "pkg/a.py": "from . import b\nfrom .sub import deep\n",
                "pkg/b.py": "",
                "pkg/sub/__init__.py": "",
                "pkg/sub/deep.py": "",
            })
            graph = build_graph(root)
            self.assertEqual(graph.edges["pkg.a"], {"pkg.b", "pkg.sub.deep"})

    def test_detects_real_circular_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, {
                "pkg/__init__.py": "",
                "pkg/a.py": "from pkg import b\n",
                "pkg/b.py": "from pkg import a\n",
            })
            graph = build_graph(root)
            self.assertEqual(graph.edges["pkg.a"], {"pkg.b"})
            self.assertEqual(graph.edges["pkg.b"], {"pkg.a"})

    def test_skips_unparseable_files_but_keeps_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, {
                "good.py": "import broken\n",
                "broken.py": "def oops(:\n",  # invalid syntax
            })
            graph = build_graph(root)
            self.assertIn("broken", graph.modules)
            self.assertEqual(graph.edges["broken"], set())
            self.assertEqual(graph.edges["good"], {"broken"})


if __name__ == "__main__":
    unittest.main()

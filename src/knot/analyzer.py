"""Static analysis of Python imports into an internal dependency graph.

The analyzer never imports or executes target code. It walks the source tree,
maps every ``.py`` file to its fully-qualified module name, parses each file
with :mod:`ast`, and resolves each ``import`` / ``from ... import`` statement to
the internal module it refers to (external imports are ignored).
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

DEFAULT_EXCLUDES: Tuple[str, ...] = (
    ".git", ".hg", ".svn", ".tox", ".nox", ".venv", "venv", "env",
    "__pycache__", ".mypy_cache", ".pytest_cache", "build", "dist",
    "node_modules", ".eggs",
)


@dataclass
class Module:
    """A single discovered module."""

    name: str
    path: Path
    is_package: bool


@dataclass
class ImportGraph:
    """The resolved internal import graph of a project."""

    modules: Dict[str, Module] = field(default_factory=dict)
    edges: Dict[str, Set[str]] = field(default_factory=dict)
    unresolved: Dict[str, Set[str]] = field(default_factory=dict)

    def nodes(self) -> List[str]:
        return sorted(self.modules)

    def edge_count(self) -> int:
        return sum(len(targets) for targets in self.edges.values())


def _iter_python_files(root: Path, excludes: Set[str]) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in sorted(dirnames) if d not in excludes]
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield Path(dirpath) / filename


def _module_name(file_path: Path, base: Path, prefix: str) -> str:
    rel = file_path.relative_to(base)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][: -len(".py")]
    dotted = ".".join(parts)
    if prefix:
        dotted = f"{prefix}.{dotted}" if dotted else prefix
    return dotted


def discover_modules(
    path: Path, excludes: Optional[Iterable[str]] = None
) -> Dict[str, Module]:
    """Discover all modules reachable from *path*.

    If *path* is a package directory (contains ``__init__.py``) its directory
    name becomes the top-level prefix, mirroring how the package is imported.
    """
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(str(path))
    exclude_set = set(DEFAULT_EXCLUDES) | set(excludes or ())

    if path.is_file():
        base, prefix = path.parent, ""
        files: Iterable[Path] = [path]
    else:
        if (path / "__init__.py").exists():
            base, prefix = path, path.name
        else:
            base, prefix = path, ""
        files = _iter_python_files(path, exclude_set)

    modules: Dict[str, Module] = {}
    for file_path in files:
        name = _module_name(file_path, base, prefix)
        if not name:
            continue
        modules[name] = Module(
            name=name, path=file_path, is_package=file_path.name == "__init__.py"
        )
    return modules


def _package_of(module: Module) -> str:
    if module.is_package:
        return module.name
    return module.name.rsplit(".", 1)[0] if "." in module.name else ""


def _resolve_absolute(target: str, module_names: Set[str]) -> Optional[str]:
    """Resolve a dotted target to the deepest matching internal module."""
    parts = target.split(".")
    for end in range(len(parts), 0, -1):
        candidate = ".".join(parts[:end])
        if candidate in module_names:
            return candidate
    return None


def _resolve_relative(
    node: ast.ImportFrom, module: Module, module_names: Set[str]
) -> List[str]:
    """Resolve a relative ``from . import x`` style statement."""
    anchor_parts = _package_of(module).split(".") if _package_of(module) else []
    climb = node.level - 1
    if climb > 0:
        anchor_parts = anchor_parts[:-climb] if climb <= len(anchor_parts) else []
    anchor = ".".join(anchor_parts)

    base = f"{anchor}.{node.module}" if node.module else anchor
    base = base.strip(".")

    resolved: List[str] = []
    if not node.module:
        for alias in node.names:
            candidate = f"{base}.{alias.name}" if base else alias.name
            hit = _resolve_absolute(candidate, module_names)
            if hit:
                resolved.append(hit)
        return resolved
    if base:
        for alias in node.names:
            candidate = f"{base}.{alias.name}"
            hit = _resolve_absolute(candidate, module_names)
            if hit:
                resolved.append(hit)
    return resolved


def _extract_targets(
    tree: ast.AST, module: Module, module_names: Set[str]
) -> Tuple[Set[str], Set[str]]:
    """Return (internal_targets, unresolved_targets) for one module."""
    internal: Set[str] = set()
    unresolved: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hit = _resolve_absolute(alias.name, module_names)
                if hit:
                    internal.add(hit)
                else:
                    unresolved.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                hits = _resolve_relative(node, module, module_names)
                if hits:
                    internal.update(hits)
                else:
                    dots = "." * node.level
                    unresolved.add(f"{dots}{node.module or ''}")
            elif node.module:
                # ``from pkg import x`` -> x may be a submodule (pkg.x) or an
                # attribute of pkg. Prefer the submodule when it exists.
                module_is_internal = _resolve_absolute(node.module, module_names)
                matched = False
                for alias in node.names:
                    candidate = f"{node.module}.{alias.name}"
                    sub = _resolve_absolute(candidate, module_names)
                    if sub:
                        internal.add(sub)
                        matched = True
                    elif module_is_internal:
                        internal.add(module_is_internal)
                        matched = True
                if not matched:
                    unresolved.add(node.module)

    internal.discard(module.name)
    return internal, unresolved


def build_graph(
    path, excludes: Optional[Iterable[str]] = None
) -> ImportGraph:
    """Build the internal :class:`ImportGraph` for the project at *path*.

    Files that fail to parse (e.g. Python 2 syntax) are skipped; their names
    still appear as nodes so the rest of the graph stays intact.
    """
    root = Path(path)
    modules = discover_modules(root, excludes)
    module_names = set(modules)

    graph = ImportGraph(modules=modules)
    for name, module in modules.items():
        graph.edges[name] = set()
        try:
            source = module.path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(module.path))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        internal, unresolved = _extract_targets(tree, module, module_names)
        graph.edges[name] = internal
        if unresolved:
            graph.unresolved[name] = unresolved
    return graph

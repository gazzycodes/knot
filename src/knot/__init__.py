"""knot — detect and visualize circular imports in Python projects.

knot statically analyzes a project's ``import`` statements (without importing
or executing any of your code), builds the internal module dependency graph,
and reports any import cycles. It is dependency-free and CI-friendly.
"""

from knot.analyzer import ImportGraph, build_graph
from knot.graph import Cycle, find_cycles

__all__ = ["ImportGraph", "build_graph", "Cycle", "find_cycles", "__version__"]

__version__ = "0.1.0"

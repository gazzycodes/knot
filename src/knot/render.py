"""Output formatters for analysis results: text, JSON, and Mermaid."""

from __future__ import annotations

import json
from typing import List

from knot.analyzer import ImportGraph
from knot.graph import Cycle


def render_text(graph: ImportGraph, cycles: List[Cycle]) -> str:
    """Human-readable report (used for the default terminal output)."""
    lines: List[str] = []
    lines.append(
        f"Analyzed {len(graph.modules)} modules, {graph.edge_count()} internal imports."
    )
    if not cycles:
        lines.append("No circular imports found.")
        return "\n".join(lines)

    noun = "cycle" if len(cycles) == 1 else "cycles"
    lines.append(f"Found {len(cycles)} import {noun}:")
    for i, cycle in enumerate(cycles, start=1):
        lines.append("")
        lines.append(f"  {i}. {' -> '.join(cycle.example_path)}")
        if cycle.size > len(set(cycle.example_path)):
            others = ", ".join(cycle.members)
            lines.append(f"     ({cycle.size} modules in this cycle: {others})")
    return "\n".join(lines)


def render_json(graph: ImportGraph, cycles: List[Cycle]) -> str:
    """Machine-readable JSON report."""
    payload = {
        "summary": {
            "modules": len(graph.modules),
            "internal_imports": graph.edge_count(),
            "cycles": len(cycles),
        },
        "cycles": [
            {"members": c.members, "example_path": c.example_path}
            for c in cycles
        ],
        "graph": {name: sorted(targets) for name, targets in graph.edges.items()},
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def render_mermaid(graph: ImportGraph, cycles: List[Cycle]) -> str:
    """A Mermaid ``graph LR`` definition, with cycle members highlighted."""
    in_cycle = {m for cycle in cycles for m in cycle.members}

    def node_id(name: str) -> str:
        return "m_" + name.replace(".", "_").replace("-", "_")

    lines: List[str] = ["graph LR"]
    for name in graph.nodes():
        lines.append(f'    {node_id(name)}["{name}"]')
    for src in graph.nodes():
        for dst in sorted(graph.edges.get(src, ())):
            lines.append(f"    {node_id(src)} --> {node_id(dst)}")
    if in_cycle:
        lines.append("    classDef cycle fill:#ffd6d6,stroke:#d33,stroke-width:2px;")
        members = ",".join(node_id(m) for m in sorted(in_cycle))
        lines.append(f"    class {members} cycle;")
    return "\n".join(lines)


def render(fmt: str, graph: ImportGraph, cycles: List[Cycle]) -> str:
    """Dispatch to the formatter named *fmt*."""
    formatters = {
        "text": render_text,
        "json": render_json,
        "mermaid": render_mermaid,
    }
    try:
        return formatters[fmt](graph, cycles)
    except KeyError:  # pragma: no cover - guarded by argparse choices
        raise ValueError(f"unknown format: {fmt!r}")

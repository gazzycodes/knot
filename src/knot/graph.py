"""Cycle detection over the import graph.

Strongly connected components (SCCs) are found with an iterative implementation
of Tarjan's algorithm (iterative to avoid recursion limits on large graphs).
Any SCC containing more than one node — or a single node with a self-edge —
is an import cycle. For each cycle a concrete example path is also extracted to
make the report actionable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class Cycle:
    """A detected import cycle."""

    members: List[str]
    """All modules participating in the cycle, sorted."""

    example_path: List[str]
    """A concrete cycle, e.g. ``[a, b, c, a]`` (first node repeated at the end)."""

    @property
    def size(self) -> int:
        return len(self.members)


def strongly_connected_components(edges: Dict[str, Set[str]]) -> List[List[str]]:
    """Return the SCCs of *edges* using an iterative Tarjan's algorithm."""
    index_of: Dict[str, int] = {}
    low_link: Dict[str, int] = {}
    on_stack: Dict[str, bool] = {}
    stack: List[str] = []
    result: List[List[str]] = []
    counter = 0

    nodes = sorted(edges)
    for start in nodes:
        if start in index_of:
            continue
        # work stack holds (node, iterator-position) frames.
        work: List[tuple] = [(start, 0)]
        while work:
            node, child_idx = work[-1]
            if child_idx == 0:
                index_of[node] = counter
                low_link[node] = counter
                counter += 1
                stack.append(node)
                on_stack[node] = True

            neighbors = sorted(edges.get(node, ()))
            if child_idx < len(neighbors):
                work[-1] = (node, child_idx + 1)
                child = neighbors[child_idx]
                if child not in index_of:
                    work.append((child, 0))
                elif on_stack.get(child):
                    low_link[node] = min(low_link[node], index_of[child])
            else:
                # Finished exploring node's children.
                if low_link[node] == index_of[node]:
                    component: List[str] = []
                    while True:
                        w = stack.pop()
                        on_stack[w] = False
                        component.append(w)
                        if w == node:
                            break
                    result.append(component)
                work.pop()
                if work:
                    parent = work[-1][0]
                    low_link[parent] = min(low_link[parent], low_link[node])
    return result


def _example_path(members: Set[str], edges: Dict[str, Set[str]]) -> List[str]:
    """Find one concrete cycle within an SCC via DFS for a back-edge."""
    start = sorted(members)[0]
    stack: List[str] = [start]
    visited: Set[str] = set()

    def dfs(node: str) -> List[str]:
        visited.add(node)
        for nxt in sorted(edges.get(node, ())):
            if nxt not in members:
                continue
            if nxt in stack:
                # Found a cycle: trim the prefix before nxt and close the loop.
                loop = stack[stack.index(nxt):]
                return loop + [nxt]
            if nxt not in visited:
                stack.append(nxt)
                found = dfs(nxt)
                if found:
                    return found
                stack.pop()
        return []

    return dfs(start)


def find_cycles(edges: Dict[str, Set[str]]) -> List[Cycle]:
    """Return all import cycles in *edges*, largest first."""
    cycles: List[Cycle] = []
    for component in strongly_connected_components(edges):
        member_set = set(component)
        is_cycle = len(component) > 1 or (
            len(component) == 1 and component[0] in edges.get(component[0], set())
        )
        if not is_cycle:
            continue
        if len(component) == 1:
            node = component[0]
            example = [node, node]
        else:
            example = _example_path(member_set, edges)
        cycles.append(
            Cycle(members=sorted(member_set), example_path=example)
        )
    cycles.sort(key=lambda c: (-c.size, c.members[0]))
    return cycles

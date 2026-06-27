"""Lightweight fact-to-fact graph edges and traversal for related recall."""

from collections import deque
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FactEdge:
    """Directed relation between two stored facts."""

    source_id: str
    target_id: str
    relation: str = "related"


@dataclass
class FactGraph:
    """In-memory adjacency list of fact edges."""

    edges: list[FactEdge] = field(default_factory=list)

    def link(self, source_id: str, target_id: str, relation: str = "related") -> FactEdge:
        edge = FactEdge(source_id=source_id, target_id=target_id, relation=relation)
        self.edges.append(edge)
        return edge

    def neighbors(self, fact_id: str) -> list[tuple[str, str]]:
        """Return ``(neighbor_id, relation)`` pairs reachable from ``fact_id``."""
        found: list[tuple[str, str]] = []
        for edge in self.edges:
            if edge.source_id == fact_id:
                found.append((edge.target_id, edge.relation))
            elif edge.target_id == fact_id:
                found.append((edge.source_id, edge.relation))
        return found

    def traverse(
        self,
        seed_ids: set[str],
        *,
        max_depth: int = 2,
        active_ids: set[str] | None = None,
    ) -> list[tuple[int, str, str]]:
        """BFS from ``seed_ids`` up to ``max_depth``, optionally filtering to active facts.

        Returns ``(depth, fact_id, relation)`` tuples in breadth-first order.
        Seeds are depth 0 and are not included in the output.
        """
        if max_depth < 1:
            return []

        visited = set(seed_ids)
        queue: deque[tuple[int, str]] = deque((0, seed_id) for seed_id in seed_ids)
        results: list[tuple[int, str, str]] = []

        while queue:
            depth, current = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor_id, relation in self.neighbors(current):
                if neighbor_id in visited:
                    continue
                if active_ids is not None and neighbor_id not in active_ids:
                    continue
                visited.add(neighbor_id)
                next_depth = depth + 1
                results.append((next_depth, neighbor_id, relation))
                queue.append((next_depth, neighbor_id))

        return results

# ADR 0006: Graph-Edge Fact Linking

## Status

Accepted

## Context

The harness already stored subject-level string edges (`link("graph", "memory")`) and
surfaced them in lexical `retrieve()`. That does not connect concrete `TemporalFact`
rows, so related beliefs discovered at different times cannot be walked during recall.
Graphiti-style systems model entity edges explicitly; this harness needs a minimal,
in-memory equivalent without a graph database.

## Decision

- Add `FactEdge` and `FactGraph` in `graph.py` with directed edges between
  `fact_id` values and undirected BFS traversal up to `max_depth`.
- Expose `link_facts(source_id, target_id, relation="related")` on `MemoryHarness`;
  reject unknown fact ids at link time.
- Add `recall_related(fact_id, max_depth=2)` for an explicit traversal-based recall
  path over active facts at a point in time.
- When `retrieve()` matches facts lexically, walk one hop of fact edges (depth 2)
  and append related active facts with a depth-decayed score. Subject-level string
  edges remain unchanged for backward compatibility.

## Consequences

- Related facts surface during hybrid retrieval without duplicating text in every
  fact row.
- Traversal is bounded, deterministic, and filters to `active_facts_at` so
  invalidated facts never appear as related results.
- Edges are stored in-process only; persistence and entity extraction belong in
  later adapters.
- String `link()` and `link_facts()` coexist — callers choose subject tags vs
  concrete fact relations.

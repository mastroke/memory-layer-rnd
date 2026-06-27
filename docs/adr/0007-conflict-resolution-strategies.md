# ADR 0007: Conflict-Resolution Strategies

## Status

Accepted

## Context

ADR 0002 introduced contradiction invalidation: a newer contradicting write
supersedes active facts on the same subject. Production agents sometimes need
that behavior (ingest order wins) and sometimes need to keep a high-confidence
belief even when a weaker extractor emits a later contradiction.

## Decision

- Add `ConflictStrategy` with `last_write_wins` (default) and
  `confidence_weighted`.
- Store `confidence` on each `TemporalFact` (default `1.0`); pass it through
  `add_fact(..., confidence=...)`.
- Centralize contradiction handling in `resolve_contradiction()`:
  - **Last-write-wins** — incoming contradicting writes always invalidate
    conflicting active facts and are stored (`action="superseded"`).
  - **Confidence-weighted** — compare `(confidence, valid_at)` tuples. Higher
    rank wins; equal rank falls back to last-write-wins. Weaker incoming writes
    return `action="rejected"` without storing a new row.
- Configure via `MemoryHarness(conflict_strategy=...)`.

## Consequences

- Callers can benchmark trust policies without changing temporal invalidation
  semantics or point-in-time replay.
- Rejected writes leave provenance unchanged; superseded rows still link via
  `linked_ids` as before.
- Confidence is a harness-level scalar, not a calibrated model score — adapters
  can map extractor logits into `[0, 1]` later.

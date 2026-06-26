# ADR 0004: Semantic Dedup On Write

## Status

Accepted

## Context

Hash dedup in `add_fact()` blocks byte-identical facts but agents often restate the
same belief with small wording drift (`"prefers python fastapi docker"` vs
`"user prefers python fastapi and docker"`). Without a semantic gate the harness
stores redundant active facts under the same subject, bloating retrieval and
making contradiction handling noisier.

## Decision

- Add lexical near-duplicate detection in `dedup.py` using token overlap
  coefficient: shared tokens divided by the smaller token-set size, threshold
  `0.8` by default.
- On write, after exact hash dedup, scan active facts for the same subject only.
  When a near-duplicate is found and the incoming text does not contradict
  existing facts, merge into the existing `TemporalFact` (refresh `valid_at`,
  prefer the longer wording) and return `action="merged"`.
- Contradictions still take precedence: if any active fact on the subject
  contradicts the incoming text, skip semantic merge and run invalidation as
  before.

## Consequences

- Restated facts under one subject collapse to a single active row instead of
  near-copies.
- Dedup stays deterministic, embedding-free, and scoped per subject — the same
  wording on different subjects remains distinct.
- Lexical overlap can miss paraphrases with disjoint vocabulary; embedding-based
  dedup belongs in a later adapter, not this harness pass.

# ADR 0005: Time-Decay Invalidation Policy

## Status

Accepted

## Context

Contradiction invalidation (ADR 0002) handles explicit supersession, and
recency weighting (ADR 0003) biases retrieval toward fresher evidence without
removing stale facts from the active set. Long-running agents also need a policy
for facts that were never contradicted but are no longer trustworthy purely
because of age — Graphiti-style temporal truth without an infinite active window.

## Decision

- Add `decay.py` with a shared exponential decay curve: weight `1.0` at age
  zero, halving every `half_life_days`.
- Configure `MemoryHarness(decay_half_life_days=N,
  decay_invalidation_threshold=0.5)`. When half-life is set, `active_facts_at`
  excludes facts whose decay weight falls below the threshold. Explicit
  `invalid_at` from contradiction handling still takes precedence.
- Expose `fact_decay_weight()` for inspection and unit tests of the curve.

## Consequences

- Stale-but-uncontradicted facts drop out of the active set deterministically;
  the underlying `TemporalFact` rows remain for point-in-time replay.
- Decay is off by default (`decay_half_life_days=None`), preserving existing
  benchmarks and callers.
- Retrieval recency boosts reuse the same decay function, so invalidation and
  ranking share one curve definition.
- Threshold defaults to `0.5`, so a fact typically invalidates shortly after one
  half-life unless callers tighten or loosen the cutoff.

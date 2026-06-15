# ADR 0002: Adopt Scoped And Temporal Memory Contracts

## Status

Accepted

## Context

Upstream memory systems solve different problems:

- Mem0 optimizes scoped personalization and additive fact storage.
- Graphiti optimizes temporal truth and contradiction handling.
- Letta optimizes tiered in-context memory for long-running agents.

## Decision

Extend the harness with:

- `SessionScope` for user/agent/run isolation
- `TemporalFact` with `valid_at` and `invalid_at`
- `CoreBlock` for always-visible structured memory
- Point-in-time retrieval and episode windows

## Consequences

- Memory behavior becomes easier to benchmark across time.
- The repository can evolve adapters without changing its public contracts.
- Full upstream complexity remains outside the first implementation pass.

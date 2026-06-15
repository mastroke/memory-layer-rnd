# ADR 0001: Make Memory Testable

## Status

Accepted

## Context

Agent memory is often described in product language but rarely tested as an engineering contract.

## Decision

Represent memory behavior with small deterministic stores and tests before adding vector databases or graph services.

## Consequences

- Memory quality can be reasoned about before infrastructure is added.
- Conflict resolution is visible and reviewable.
- Future adapters can preserve the same behavioral tests.


# ADR 0003: Recency Weighting And Recall Compaction

## Status

Accepted

## Context

The first pass gave the harness scope, temporal truth and hybrid retrieval, but
two long-running-agent concerns were still open and listed on the evolution path:

- Retrieval ranked purely on lexical overlap, so a stale fact and a fresh fact
  with identical wording tied. Production memory systems (Mem0 score fusion,
  generative-agents recency decay) bias toward fresher evidence.
- Episode history grew unbounded in the active window. Letta compacts older
  recall into summaries so the in-context surface stays small while provenance is
  retained.

## Decision

- Add an opt-in exponential recency boost to `retrieve()` via
  `recency_half_life_days`. A memory `half_life_days` old keeps half its lexical
  score; future-dated events get no boost; `None` preserves the original
  lexical-only ranking for backward compatibility.
- Add `compact_episodes(keep_recent=N)` that folds older episodes into a
  read-only `recall_summary` block and moves the originals to
  `archived_episodes`, returning a `CompactionResult`.

## Consequences

- Retrieval can prefer fresher facts without discarding lexical relevance, and
  the behavior is deterministic and unit-tested.
- Long episode streams stay bounded in the active window while summaries and
  archived originals preserve traceability.
- Recency weighting stays off by default, so existing callers and benchmarks are
  unaffected unless they opt in.
- Compaction is summary-based, not detail-preserving, in the active window; the
  archival list is the source of record for the compacted span.

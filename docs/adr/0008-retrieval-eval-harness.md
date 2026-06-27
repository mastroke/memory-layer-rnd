# ADR 0008: Retrieval Evaluation Harness

## Status

Accepted

## Context

Hybrid `retrieve()` now fuses lexical overlap, recency boosts, graph neighbors,
blocks and episodes. Unit tests assert individual behaviors, but there was no
small, repeatable benchmark to compare ranking strategies or catch regressions
when scoring changes.

## Decision

- Add set-based precision, recall and F1 in `retrieval_metrics.py`, keyed by
  stable fixture labels rather than runtime `fact_id` values.
- Add `retrieval_eval.py` with declarative `RetrievalEvalCase` fixtures,
  `evaluate_case()` for one query/strategy pair, and `compare_strategies()` for
  aggregated means across the default fixture pack.
- Ship four default cases: lexical focus, recency tie-break at top-1, graph
  neighbor recall, and multi-source (fact + block + episode) coverage.
- Expose `lexical`, `recency_30d`, and matching `*_top1` strategies so
  full-list recall and rank-sensitive precision can both be measured.

## Consequences

- Retrieval ranking changes can be gated on fixture metrics before larger
  LongMemEval-style replays land.
- Fixture keys decouple evaluation from UUID fact ids while still parsing
  `retrieve()` result lines deterministically.
- The harness is in-process and dependency-free; it does not prescribe an
  external dataset format yet.
- Set-based metrics treat all hits in the retrieved window equally; MRR or
  nDCG would be a separate addition if rank shape needs finer grading.

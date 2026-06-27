# Upstream Learning Notes

This repository studies patterns from three widely used memory systems. Forks live under [@mastroke](https://github.com/mastroke):

| Upstream | Fork | Stars (approx.) | What we studied |
| --- | --- | --- | --- |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | [mastroke/mem0](https://github.com/mastroke/mem0) | 58k+ | Scoped memory, additive extraction, hash dedup, hybrid retrieval |
| [getzep/graphiti](https://github.com/getzep/graphiti) | [mastroke/graphiti](https://github.com/mastroke/graphiti) | 27k+ | Temporal facts, episode provenance, point-in-time queries |
| [letta-ai/letta](https://github.com/letta-ai/letta) | [mastroke/letta](https://github.com/mastroke/letta) | 13k+ | Core memory blocks, recall vs archival separation |

## Mem0 patterns adopted

| Pattern | Upstream reference | Implemented here |
| --- | --- | --- |
| `user_id` / `agent_id` / `run_id` scopes | `mem0/memory/main.py` | `SessionScope` in `scopes.py` |
| Rolling message buffer for extraction context | `mem0/memory/storage.py` | `message_buffer` in `MemoryHarness` |
| ADD-only with supersede links | `mem0/configs/prompts.py` | `linked_ids` on `TemporalFact` |
| MD5 hash dedup | `mem0/memory/main.py` | `_hash_text()` in `harness.py` |
| Lexical near-duplicate merge | Mem0 dream-style merge heuristics | `near_duplicate()` + write-path merge in `harness.py` |
| Hybrid retrieval fusion | `mem0/utils/scoring.py` | `retrieve()` scoring in `harness.py` |

## Graphiti patterns adopted

| Pattern | Upstream reference | Implemented here |
| --- | --- | --- |
| `valid_at` / `invalid_at` fact validity | `graphiti_core/edges.py` | `TemporalFact` in `temporal.py` |
| Episode `reference_time` | `graphiti_core/graphiti.py` | `Episode.reference_time` |
| Point-in-time active facts | `search/search_filters.py` | `active_facts_at()` |
| Time-decay invalidation of stale facts | temporal edge decay patterns | `decay_half_life_days` on `MemoryHarness` |
| Contradiction invalidation instead of delete | `edge_operations.py` | `add_fact(invalidate_conflicts=True)` |
| Episode window before current time | `graph_data_operations.py` | `episodes_before()` |

## Letta patterns adopted

| Pattern | Upstream reference | Implemented here |
| --- | --- | --- |
| Labeled core blocks | `letta/schemas/block.py` | `CoreBlock` in `blocks.py` |
| Block metadata in prompt surface | `letta/schemas/memory.py` | `CoreBlock.render()` |
| Out-of-context memory metadata | `letta/prompts/prompt_generator.py` | `metadata()` |
| Tier separation: blocks vs episodes vs facts | `memgpt_v2_chat.py` | `MemoryHarness` stores |
| Recall compaction of overflowing history | `letta/services/summarizer/` | `compact_episodes()` in `harness.py` |

## Cross-cutting retrieval patterns

| Pattern | Upstream reference | Implemented here |
| --- | --- | --- |
| Recency-weighted memory ranking | generative-agents `retrieve()` recency decay; Mem0 score fusion | `_recency_weight()` + `retrieve(recency_half_life_days=...)` |
| Time-decay fact invalidation | Graphiti temporal edge aging | `decay.py` + `decay_half_life_days` on `MemoryHarness` |

## What is intentionally not ported yet

- Mem0 LLM extraction and spaCy entity graph
- Graphiti Neo4j graph engine and full hybrid search stack
- Letta sleeptime agents, archival embeddings and Postgres persistence

Those belong in later adapters once the harness contracts are stable.

## Suggested reading order

1. Mem0 `memory/main.py` — write path and scope filters
2. Graphiti `graphiti_core/graphiti.py` — `add_episode()` lifecycle
3. Letta `letta/schemas/memory.py` — block compilation model

## Next implementation targets

- LongMemEval-style fixture replay
- Optional Mem0 adapter behind `MemoryHarness`
- Graphiti-style entity edge retrieval boosts
- ~~Letta-style recall compaction for long episode windows~~ — shipped via `compact_episodes()`
- ~~Recency-weighted retrieval scoring~~ — shipped via `recency_half_life_days`
- ~~Time-decay invalidation for stale active facts~~ — shipped via `decay_half_life_days`

"""Memory-as-contract boundary definitions for the research harness.

See ADR 0009 for rationale and the full guarantee/refusal tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MemoryTier(str, Enum):
    """Durable memory tiers the harness exposes through typed write APIs."""

    FACT = "fact"
    EPISODE = "episode"
    BLOCK = "block"
    LEXICAL_GRAPH = "lexical_graph"
    FACT_GRAPH = "fact_graph"
    ARCHIVED_EPISODE = "archived_episode"


class RefusedContent(str, Enum):
    """Content categories the harness refuses to treat as durable memory."""

    RAW_TRANSCRIPT = "raw_transcript"
    UNSCOPED_WRITE = "unscoped_write"
    IMPLICIT_TIER = "implicit_tier"
    CROSS_SUBJECT_SEMANTIC_DEDUP = "cross_subject_semantic_dedup"
    EMBEDDING_INDEX = "embedding_index"
    LLM_EXTRACTION = "llm_extraction"
    CALIBRATED_CONFIDENCE = "calibrated_confidence"
    FULL_NLU_CONTRADICTION = "full_nlu_contradiction"
    BINARY_MEDIA = "binary_media"
    UNBOUNDED_ACTIVE_EPISODES = "unbounded_active_episodes"
    PERSISTENT_STORAGE = "persistent_storage"
    SECRETS_VAULT = "secrets_vault"


class FactWriteAction(str, Enum):
    """Explicit outcomes from ``MemoryHarness.add_fact()``."""

    CREATED = "created"
    DUPLICATE = "duplicate"
    MERGED = "merged"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


@dataclass(frozen=True)
class MemoryGuarantee:
    """One contract guarantee callers can rely on."""

    name: str
    description: str


@dataclass(frozen=True)
class MemoryRefusal:
    """One contract refusal — content or semantics the layer will not promise."""

    category: RefusedContent
    description: str
    caller_alternative: str


# Canonical lists referenced by tests and documentation (ADR 0009).
MEMORY_GUARANTEES: tuple[MemoryGuarantee, ...] = (
    MemoryGuarantee(
        name="explicit_write_outcomes",
        description="add_fact() returns AddFactResult.action in FactWriteAction values.",
    ),
    MemoryGuarantee(
        name="scope_before_storage",
        description="Episodes carry SessionScope; facts and blocks live in a scoped harness.",
    ),
    MemoryGuarantee(
        name="temporal_truth",
        description="active_facts_at(T) reflects valid_at/invalid_at, not only current rows.",
    ),
    MemoryGuarantee(
        name="contradiction_invalidation",
        description="Conflicting active facts on the same subject resolve via ConflictStrategy.",
    ),
    MemoryGuarantee(
        name="dedup_on_write",
        description="Exact duplicates return duplicate; near-duplicates merge per subject.",
    ),
    MemoryGuarantee(
        name="tier_appropriate_retrieval",
        description="retrieve() searches facts, graph, episodes, and blocks — not internal buffers.",
    ),
    MemoryGuarantee(
        name="deterministic_in_process",
        description="Contract behavior is testable without vector DB, graph DB, or LLM services.",
    ),
)

MEMORY_REFUSALS: tuple[MemoryRefusal, ...] = (
    MemoryRefusal(
        category=RefusedContent.RAW_TRANSCRIPT,
        description="message_buffer is extraction context only; not indexed or retrieved.",
        caller_alternative="remember_episode() for durable events; external log for full transcripts.",
    ),
    MemoryRefusal(
        category=RefusedContent.UNSCOPED_WRITE,
        description="SessionScope requires at least one of user_id, agent_id, run_id.",
        caller_alternative="Construct SessionScope before MemoryHarness.",
    ),
    MemoryRefusal(
        category=RefusedContent.IMPLICIT_TIER,
        description="No untyped store-this-string API; callers pick a tier write path.",
        caller_alternative="add_fact(), remember_episode(), or upsert_block().",
    ),
    MemoryRefusal(
        category=RefusedContent.CROSS_SUBJECT_SEMANTIC_DEDUP,
        description="Near-duplicate merge applies within one subject only.",
        caller_alternative="Normalize subjects upstream or use an embedding adapter.",
    ),
    MemoryRefusal(
        category=RefusedContent.EMBEDDING_INDEX,
        description="Retrieval uses lexical overlap, not vector similarity.",
        caller_alternative="Adapter behind retrieve() with eval fixtures (ADR 0008).",
    ),
    MemoryRefusal(
        category=RefusedContent.LLM_EXTRACTION,
        description="No automatic entity or relation extraction on ingest.",
        caller_alternative="Caller or Mem0 adapter supplies (subject, fact) pairs.",
    ),
    MemoryRefusal(
        category=RefusedContent.CALIBRATED_CONFIDENCE,
        description="confidence is caller-provided, not a calibrated model score.",
        caller_alternative="Map extractor output in an adapter.",
    ),
    MemoryRefusal(
        category=RefusedContent.FULL_NLU_CONTRADICTION,
        description="_contradicts() uses negation tokens and prefix heuristics only.",
        caller_alternative="Stronger NLU belongs outside the harness.",
    ),
    MemoryRefusal(
        category=RefusedContent.BINARY_MEDIA,
        description="Stores text strings only.",
        caller_alternative="Store references (URIs, ids) as facts.",
    ),
    MemoryRefusal(
        category=RefusedContent.UNBOUNDED_ACTIVE_EPISODES,
        description="Long histories require compact_episodes(); active window is bounded.",
        caller_alternative="Compact or archive; provenance stays in archived_episodes.",
    ),
    MemoryRefusal(
        category=RefusedContent.PERSISTENT_STORAGE,
        description="In-memory lists and dicts; no replication or durability.",
        caller_alternative="Wrap harness or sync to external store in an adapter.",
    ),
    MemoryRefusal(
        category=RefusedContent.SECRETS_VAULT,
        description="No encryption, redaction, or vault semantics for sensitive strings.",
        caller_alternative="Redact before write; use a dedicated secrets store.",
    ),
)

DURABLE_TIERS: frozenset[MemoryTier] = frozenset(MemoryTier)
FACT_WRITE_ACTIONS: frozenset[str] = frozenset(action.value for action in FactWriteAction)


def message_buffer_is_retrieval_excluded() -> bool:
    """Return True — message_buffer must never appear in retrieve() results."""
    return True

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from memory_layer_rnd.memory import MemoryStore
from memory_layer_rnd.temporal import TemporalFact


class ConflictStrategy(str, Enum):
    """How to pick the active fact when a new write contradicts existing ones."""

    LAST_WRITE_WINS = "last_write_wins"
    CONFIDENCE_WEIGHTED = "confidence_weighted"


@dataclass(frozen=True)
class Resolution:
    action: str
    subject: str
    previous: str | None
    current: str


@dataclass(frozen=True)
class ContradictionOutcome:
    """Result of applying a conflict strategy to contradicting facts."""

    action: str
    store_incoming: bool
    invalidate_ids: list[str]
    prevailing_fact_id: str | None = None


def resolve_fact(store: MemoryStore, subject: str, new_fact: str) -> Resolution:
    key = subject.lower()
    previous = store.semantic.get(key)

    if previous == new_fact:
        return Resolution(action="unchanged", subject=key, previous=previous, current=new_fact)

    store.upsert_fact(subject=key, fact=new_fact)
    return Resolution(
        action="updated" if previous else "created",
        subject=key,
        previous=previous,
        current=new_fact,
    )


def _fact_rank(fact: TemporalFact) -> tuple[float, datetime]:
    return (fact.confidence, fact.valid_at)


def resolve_contradiction(
    *,
    strategy: ConflictStrategy,
    conflicting: list[TemporalFact],
    incoming_time: datetime,
    incoming_confidence: float,
) -> ContradictionOutcome:
    """Pick whether an incoming contradicting write is stored and what it invalidates."""
    if not conflicting:
        return ContradictionOutcome(action="created", store_incoming=True, invalidate_ids=[])

    if strategy == ConflictStrategy.LAST_WRITE_WINS:
        return ContradictionOutcome(
            action="superseded",
            store_incoming=True,
            invalidate_ids=[fact.fact_id for fact in conflicting],
        )

    champion = max(conflicting, key=_fact_rank)
    incoming_rank = (incoming_confidence, incoming_time)
    champion_rank = _fact_rank(champion)

    if incoming_rank > champion_rank:
        return ContradictionOutcome(
            action="superseded",
            store_incoming=True,
            invalidate_ids=[fact.fact_id for fact in conflicting],
        )
    if incoming_rank < champion_rank:
        return ContradictionOutcome(
            action="rejected",
            store_incoming=False,
            invalidate_ids=[],
            prevailing_fact_id=champion.fact_id,
        )

    # Equal confidence and reference time: incoming write wins (last-write-wins tie-break).
    return ContradictionOutcome(
        action="superseded",
        store_incoming=True,
        invalidate_ids=[fact.fact_id for fact in conflicting],
    )

"""Tests for memory-as-contract boundaries (ADR 0009)."""

import pytest

from memory_layer_rnd.contract import (
    DURABLE_TIERS,
    FACT_WRITE_ACTIONS,
    MEMORY_GUARANTEES,
    MEMORY_REFUSALS,
    FactWriteAction,
    MemoryTier,
    RefusedContent,
    message_buffer_is_retrieval_excluded,
)
from memory_layer_rnd.harness import MemoryHarness
from memory_layer_rnd.resolver import ConflictStrategy
from memory_layer_rnd.scopes import SessionScope


def test_contract_catalogues_guarantees_and_refusals() -> None:
    assert len(MEMORY_GUARANTEES) >= 5
    assert len(MEMORY_REFUSALS) >= 10
    assert DURABLE_TIERS == frozenset(MemoryTier)
    assert FACT_WRITE_ACTIONS == frozenset(action.value for action in FactWriteAction)


def test_unscoped_session_rejected() -> None:
    with pytest.raises(ValueError, match="At least one scope identifier"):
        SessionScope()


def test_message_buffer_excluded_from_retrieval() -> None:
    """message_buffer is context-only; retrieve() must not surface it."""
    assert message_buffer_is_retrieval_excluded()

    harness = MemoryHarness(scope=SessionScope(user_id="u1"))
    harness.message_buffer.append("secret buffer-only extraction context")
    harness.add_fact("topic", "durable graph memory", reference_time="2026-06-01T10:00:00+00:00")

    results = harness.retrieve("secret buffer extraction context graph memory")

    assert harness.message_buffer
    assert not any("secret buffer-only" in line for line in results)
    assert any(line.startswith("fact[") for line in results)


def test_fact_write_actions_are_explicit() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))

    created = harness.add_fact("stack", "python fastapi docker", reference_time="2026-06-01T10:00:00+00:00")
    duplicate = harness.add_fact("stack", "python fastapi docker", reference_time="2026-06-02T10:00:00+00:00")
    merged = harness.add_fact(
        "stack",
        "prefers python fastapi and docker stack",
        reference_time="2026-06-03T10:00:00+00:00",
    )
    harness.add_fact("role", "works on notebooks", reference_time="2026-06-01T10:00:00+00:00")
    superseded = harness.add_fact(
        "role",
        "works on memory systems not notebooks",
        reference_time="2026-06-10T10:00:00+00:00",
    )
    rejected_harness = MemoryHarness(
        scope=SessionScope(user_id="u1"),
        conflict_strategy=ConflictStrategy.CONFIDENCE_WEIGHTED,
    )
    rejected_harness.add_fact(
        "focus",
        "vector memory research",
        reference_time="2026-06-01T10:00:00+00:00",
        confidence=0.9,
    )
    rejected = rejected_harness.add_fact(
        "focus",
        "vector memory research is not priority",
        reference_time="2026-06-15T10:00:00+00:00",
        confidence=0.3,
    )

    observed = {created.action, duplicate.action, merged.action, superseded.action, rejected.action}
    assert observed.issubset(FACT_WRITE_ACTIONS)
    assert created.action == FactWriteAction.CREATED.value
    assert duplicate.action == FactWriteAction.DUPLICATE.value
    assert merged.action == FactWriteAction.MERGED.value
    assert superseded.action == FactWriteAction.SUPERSEDED.value
    assert rejected.action == FactWriteAction.REJECTED.value


def test_refusal_categories_are_unique() -> None:
    categories = [refusal.category for refusal in MEMORY_REFUSALS]
    assert len(categories) == len(set(categories))
    assert RefusedContent.RAW_TRANSCRIPT in categories

import pytest

from memory_layer_rnd.decay import decay_weight_for_age, temporal_decay_weight
from memory_layer_rnd.harness import MemoryHarness
from memory_layer_rnd.scopes import SessionScope
from memory_layer_rnd.temporal import utc_now


def test_temporal_fact_invalidation() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))

    first = harness.add_fact("role", "works on notebooks", reference_time="2026-06-01T10:00:00+00:00")
    second = harness.add_fact(
        "role",
        "works on memory systems not notebooks",
        reference_time="2026-06-10T10:00:00+00:00",
    )

    assert first.action == "created"
    assert second.action == "superseded"
    assert second.invalidated == [first.fact.fact_id]

    past = harness.active_facts_at("2026-06-05T00:00:00+00:00")
    present = harness.active_facts_at("2026-06-15T00:00:00+00:00")

    assert len(past) == 1
    assert past[0].fact == "works on notebooks"
    assert len(present) == 1
    assert "memory systems" in present[0].fact


def test_hash_dedup_blocks_exact_duplicates() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))

    first = harness.add_fact("stack", "python fastapi docker")
    second = harness.add_fact("stack", "python fastapi docker")

    assert first.action == "created"
    assert second.action == "duplicate"


def test_semantic_dedup_merges_near_duplicate_facts() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))

    first = harness.add_fact(
        "stack",
        "user prefers python fastapi docker",
        reference_time="2026-06-01T10:00:00+00:00",
    )
    second = harness.add_fact(
        "stack",
        "prefers python fastapi and docker stack",
        reference_time="2026-06-05T10:00:00+00:00",
    )

    assert first.action == "created"
    assert second.action == "merged"
    assert second.fact.fact_id == first.fact.fact_id
    assert len(harness.facts) == 1
    assert len(harness.active_facts_at("2026-06-10T00:00:00+00:00")) == 1


def test_semantic_dedup_respects_subject_scope() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))

    first = harness.add_fact("stack", "python fastapi docker deployment")
    second = harness.add_fact("tooling", "python fastapi docker deployment")

    assert first.action == "created"
    assert second.action == "created"
    assert first.fact.fact_id != second.fact.fact_id
    assert len(harness.facts) == 2


def test_scope_key_is_deterministic() -> None:
    scope = SessionScope(user_id="u1", agent_id="a1", run_id="r1")
    assert "user:u1" in scope.key
    assert "agent:a1" in scope.key


def test_core_blocks_render_with_metadata() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))
    block = harness.upsert_block("persona", "Agent behavior", "architecture-first")

    assert 'label="persona"' in block.render()
    assert "architecture-first" in block.render()


def test_point_in_time_episode_window() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))
    harness.remember_episode("old context", reference_time="2026-06-01T10:00:00+00:00")
    harness.remember_episode("new context", reference_time="2026-06-15T10:00:00+00:00")

    window = harness.episodes_before("2026-06-10T00:00:00+00:00")

    assert len(window) == 1
    assert window[0].text == "old context"


def test_hybrid_retrieval_returns_multiple_sources() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))
    harness.upsert_block("human", "preferences", "likes graph memory")
    harness.add_fact("topic", "graph memory retrieval", reference_time="2026-06-01T10:00:00+00:00")
    harness.link("graph", "memory")
    harness.remember_episode("Discussed graph memory patterns", reference_time="2026-06-01T10:00:00+00:00")

    results = harness.retrieve("graph memory", as_of="2026-06-15T12:00:00+00:00")

    assert any(item.startswith("fact[") for item in results)
    assert any(item.startswith("graph:") for item in results)
    assert any(item.startswith("episode@") for item in results)


def test_recency_weighting_prefers_fresher_facts() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))
    harness.add_fact("alpha", "graph memory retrieval", reference_time="2026-01-01T00:00:00+00:00")
    harness.add_fact("beta", "graph memory retrieval", reference_time="2026-06-01T00:00:00+00:00")

    as_of = "2026-06-10T00:00:00+00:00"

    lexical = harness.retrieve("graph memory retrieval", as_of=as_of)
    weighted = harness.retrieve("graph memory retrieval", as_of=as_of, recency_half_life_days=30)

    # Without recency weighting both facts tie and stable sort keeps insertion order.
    assert lexical[0].startswith("fact[") and "alpha" in lexical[0]
    # With recency weighting the fresher fact (beta) is promoted ahead of alpha.
    assert weighted[0].startswith("fact[") and "beta" in weighted[0]


def test_recency_weighting_rejects_nonpositive_half_life() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))
    harness.add_fact("alpha", "graph memory", reference_time="2026-06-01T00:00:00+00:00")

    with pytest.raises(ValueError):
        harness.retrieve("graph", as_of="2026-06-02T00:00:00+00:00", recency_half_life_days=0)


def test_decay_weight_follows_half_life_curve() -> None:
    half_life = 30.0
    assert decay_weight_for_age(0.0, half_life) == pytest.approx(1.0)
    assert decay_weight_for_age(half_life, half_life) == pytest.approx(0.5)
    assert decay_weight_for_age(2 * half_life, half_life) == pytest.approx(0.25)
    assert decay_weight_for_age(3 * half_life, half_life) == pytest.approx(0.125)


def test_temporal_decay_weight_disabled_returns_unity() -> None:
    moment = utc_now()
    assert temporal_decay_weight(moment, moment, None) == 1.0


def test_time_decay_invalidates_stale_facts() -> None:
    harness = MemoryHarness(
        scope=SessionScope(user_id="u1"),
        decay_half_life_days=30,
        decay_invalidation_threshold=0.5,
    )
    harness.add_fact("focus", "vector memory research", reference_time="2026-01-01T00:00:00+00:00")

    fresh_view = harness.active_facts_at("2026-01-20T00:00:00+00:00")
    stale_view = harness.active_facts_at("2026-02-05T00:00:00+00:00")

    assert len(fresh_view) == 1
    assert harness.fact_decay_weight(fresh_view[0], "2026-01-20T00:00:00+00:00") > 0.5
    assert len(stale_view) == 0
    assert harness.fact_decay_weight(harness.facts[0], "2026-02-05T00:00:00+00:00") < 0.5


def test_time_decay_disabled_keeps_old_facts_active() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))
    harness.add_fact("focus", "vector memory research", reference_time="2026-01-01T00:00:00+00:00")

    assert len(harness.active_facts_at("2026-12-01T00:00:00+00:00")) == 1


def test_time_decay_respects_explicit_contradiction_invalidation() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"), decay_half_life_days=365)
    harness.add_fact("role", "works on notebooks", reference_time="2026-06-01T10:00:00+00:00")
    harness.add_fact(
        "role",
        "works on memory systems not notebooks",
        reference_time="2026-06-10T10:00:00+00:00",
    )

    past = harness.active_facts_at("2026-06-05T00:00:00+00:00")
    present = harness.active_facts_at("2026-06-15T00:00:00+00:00")

    assert len(past) == 1 and "notebooks" in past[0].fact
    assert len(present) == 1 and "memory systems" in present[0].fact


def test_decay_half_life_rejects_nonpositive_config() -> None:
    with pytest.raises(ValueError):
        MemoryHarness(scope=SessionScope(user_id="u1"), decay_half_life_days=0)


def test_decay_invalidation_threshold_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        MemoryHarness(scope=SessionScope(user_id="u1"), decay_invalidation_threshold=0.0)


def test_recall_compaction_summarizes_old_episodes() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))
    for day in range(1, 9):
        harness.remember_episode(f"event number {day}", reference_time=f"2026-06-0{day}T10:00:00+00:00")

    result = harness.compact_episodes(keep_recent=3)

    assert result.archived == 5
    assert result.retained == 3
    assert len(harness.episodes) == 3
    assert len(harness.archived_episodes) == 5
    assert result.summary is not None and result.summary.read_only is True
    assert "recall_summary" in harness.blocks
    # Most recent episodes are the ones kept in the active window.
    assert harness.episodes[-1].text == "event number 8"


def test_recall_compaction_noop_when_under_threshold() -> None:
    harness = MemoryHarness(scope=SessionScope(user_id="u1"))
    harness.remember_episode("only event", reference_time="2026-06-01T10:00:00+00:00")

    result = harness.compact_episodes(keep_recent=5)

    assert result.summary is None
    assert result.archived == 0
    assert result.retained == 1
    assert "recall_summary" not in harness.blocks


def test_demo_reports_temporal_views() -> None:
    from memory_layer_rnd.demo import run_demo

    payload = run_demo()

    assert payload["metadata"]["active_fact_count"] >= 1
    assert payload["retrieval_now"]
    assert payload["active_facts_past"] != payload["active_facts_now"]

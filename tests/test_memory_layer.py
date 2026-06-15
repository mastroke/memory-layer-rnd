from memory_layer_rnd.harness import MemoryHarness
from memory_layer_rnd.scopes import SessionScope


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
    harness.add_fact("topic", "graph memory retrieval")
    harness.link("graph", "memory")
    harness.remember_episode("Discussed graph memory patterns", reference_time="2026-06-01T10:00:00+00:00")

    results = harness.retrieve("graph memory", as_of="2026-06-15T12:00:00+00:00")

    assert any(item.startswith("fact[") for item in results)
    assert any(item.startswith("graph:") for item in results)
    assert any(item.startswith("episode@") for item in results)


def test_demo_reports_temporal_views() -> None:
    from memory_layer_rnd.demo import run_demo

    payload = run_demo()

    assert payload["metadata"]["active_fact_count"] >= 1
    assert payload["retrieval_now"]
    assert payload["active_facts_past"] != payload["active_facts_now"]

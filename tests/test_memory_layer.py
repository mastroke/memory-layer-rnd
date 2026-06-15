from memory_layer_rnd.demo import run_demo
from memory_layer_rnd.memory import MemoryEvent, MemoryStore
from memory_layer_rnd.resolver import resolve_fact


def test_fact_resolution_updates_existing_memory() -> None:
    store = MemoryStore()

    created = resolve_fact(store, "focus", "agent memory")
    updated = resolve_fact(store, "focus", "agent memory and evals")

    assert created.action == "created"
    assert updated.action == "updated"
    assert updated.previous == "agent memory"
    assert store.semantic["focus"] == "agent memory and evals"


def test_retrieval_uses_multiple_memory_types() -> None:
    store = MemoryStore()
    store.remember_event(MemoryEvent(user_id="u1", text="Prefers quant research examples."))
    store.upsert_fact("role", "systems builder")
    store.link("agentic-ai", "evaluation")

    results = store.retrieve("agentic-ai quant systems")

    assert any("role" in item for item in results)
    assert any("agentic-ai" in item for item in results)
    assert any("event" in item for item in results)


def test_demo_returns_context() -> None:
    assert run_demo()


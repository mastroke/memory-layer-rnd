from memory_layer_rnd.harness import MemoryHarness
from memory_layer_rnd.scopes import SessionScope


def build_demo_harness() -> MemoryHarness:
    harness = MemoryHarness(scope=SessionScope(user_id="demo-user", agent_id="research-agent", run_id="session-1"))

    harness.upsert_block(
        label="persona",
        description="How the agent should reason about memory architecture.",
        value="Prefer explicit memory contracts, temporal invalidation and testable retrieval.",
    )
    harness.upsert_block(
        label="human",
        description="Stable preferences for the current user.",
        value="Interested in agent memory, quant systems and production ML design.",
        read_only=True,
    )

    harness.remember_episode("User asked for architecture-first memory design.", reference_time="2026-06-01T10:00:00+00:00")
    harness.remember_episode("User now wants temporal facts and upstream pattern study.", reference_time="2026-06-15T09:00:00+00:00")

    harness.add_fact("focus", "agent memory research", reference_time="2026-06-01T10:05:00+00:00")
    harness.add_fact("focus", "agent memory, temporal facts and benchmark harnesses", reference_time="2026-06-15T09:05:00+00:00")
    harness.link("agentic-ai", "memory")
    harness.link("agentic-ai", "evaluation")

    return harness


def run_demo() -> dict:
    harness = build_demo_harness()
    return {
        "metadata": harness.metadata(),
        "retrieval_now": harness.retrieve("agentic-ai memory focus"),
        "retrieval_past": harness.retrieve("focus", as_of="2026-06-02T00:00:00+00:00"),
        "active_facts_now": [f"{fact.subject}: {fact.fact}" for fact in harness.active_facts_at()],
        "active_facts_past": [
            f"{fact.subject}: {fact.fact}"
            for fact in harness.active_facts_at("2026-06-02T00:00:00+00:00")
        ],
        "blocks": [block.render() for block in harness.blocks.values()],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_demo(), indent=2))

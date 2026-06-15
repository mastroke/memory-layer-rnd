from memory_layer_rnd.memory import MemoryEvent, MemoryStore
from memory_layer_rnd.resolver import resolve_fact


def run_demo() -> list[str]:
    store = MemoryStore()
    store.remember_event(MemoryEvent(user_id="demo", text="User prefers concise architecture-focused summaries."))
    resolve_fact(store, "focus", "agentic AI and memory-layer R&D")
    resolve_fact(store, "focus", "agentic AI, MLOps and quant systems")
    store.link("agentic-ai", "memory")
    store.link("agentic-ai", "evaluation")
    return store.retrieve("agentic-ai memory focus")


if __name__ == "__main__":
    for item in run_demo():
        print(item)


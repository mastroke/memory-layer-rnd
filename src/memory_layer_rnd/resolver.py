from dataclasses import dataclass

from memory_layer_rnd.memory import MemoryStore


@dataclass(frozen=True)
class Resolution:
    action: str
    subject: str
    previous: str | None
    current: str


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


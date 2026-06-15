from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class MemoryEvent:
    user_id: str
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MemoryStore:
    episodic: list[MemoryEvent] = field(default_factory=list)
    semantic: dict[str, str] = field(default_factory=dict)
    graph: dict[str, set[str]] = field(default_factory=dict)

    def remember_event(self, event: MemoryEvent) -> None:
        self.episodic.append(event)

    def upsert_fact(self, subject: str, fact: str) -> None:
        self.semantic[subject.lower()] = fact

    def link(self, source: str, target: str) -> None:
        self.graph.setdefault(source.lower(), set()).add(target.lower())

    def retrieve(self, query: str) -> list[str]:
        terms = set(query.lower().split())
        results: list[str] = []

        for subject, fact in self.semantic.items():
            if subject in terms or terms.intersection(fact.lower().split()):
                results.append(f"{subject}: {fact}")

        for source, targets in self.graph.items():
            if source in terms or terms.intersection(targets):
                results.append(f"{source} -> {', '.join(sorted(targets))}")

        for event in self.episodic[-5:]:
            if terms.intersection(event.text.lower().split()):
                results.append(f"event: {event.text}")

        return results


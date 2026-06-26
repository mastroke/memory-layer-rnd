import hashlib
import math
import re
from dataclasses import dataclass, field

from memory_layer_rnd.blocks import CoreBlock
from memory_layer_rnd.dedup import near_duplicate
from memory_layer_rnd.scopes import SessionScope
from memory_layer_rnd.temporal import TemporalFact, utc_now


@dataclass(frozen=True)
class Episode:
    text: str
    reference_time: str
    scope: SessionScope


@dataclass(frozen=True)
class AddFactResult:
    action: str
    fact: TemporalFact
    invalidated: list[str]


@dataclass(frozen=True)
class CompactionResult:
    """Outcome of a Letta-style recall compaction pass."""

    summary: CoreBlock | None
    archived: int
    retained: int


@dataclass
class MemoryHarness:
    """Research harness combining Mem0, Graphiti and Letta patterns."""

    scope: SessionScope
    episodes: list[Episode] = field(default_factory=list)
    facts: list[TemporalFact] = field(default_factory=list)
    blocks: dict[str, CoreBlock] = field(default_factory=dict)
    graph: dict[str, set[str]] = field(default_factory=dict)
    message_buffer: list[str] = field(default_factory=list)
    archived_episodes: list[Episode] = field(default_factory=list)
    _hashes: set[str] = field(default_factory=set)

    def remember_episode(self, text: str, reference_time: str | None = None) -> Episode:
        timestamp = reference_time or utc_now().isoformat()
        episode = Episode(text=text, reference_time=timestamp, scope=self.scope)
        self.episodes.append(episode)
        self.message_buffer.append(text)
        self.message_buffer = self.message_buffer[-10:]
        return episode

    def upsert_block(self, label: str, description: str, value: str, read_only: bool = False) -> CoreBlock:
        block = CoreBlock(label=label, description=description, value=value, read_only=read_only)
        self.blocks[label] = block
        return block

    def link(self, source: str, target: str) -> None:
        self.graph.setdefault(source.lower(), set()).add(target.lower())

    @staticmethod
    def _hash_text(text: str) -> str:
        return hashlib.md5(text.strip().lower().encode()).hexdigest()

    def _active_facts_for_subject(self, subject: str) -> list[TemporalFact]:
        key = subject.lower()
        return [fact for fact in self.facts if fact.subject == key and fact.is_active]

    @staticmethod
    def _merge_near_duplicate(existing: TemporalFact, incoming: str, when) -> TemporalFact:
        """Reaffirm an active near-duplicate instead of storing a second fact."""
        if len(incoming.split()) > len(existing.fact.split()):
            existing.fact = incoming
        if when > existing.valid_at:
            existing.valid_at = when
        return existing

    def add_fact(
        self,
        subject: str,
        fact_text: str,
        reference_time: str | None = None,
        invalidate_conflicts: bool = True,
    ) -> AddFactResult:
        when = reference_time or utc_now().isoformat()
        when_dt = utc_now() if reference_time is None else _parse_time(reference_time)
        digest = self._hash_text(f"{subject}:{fact_text}")

        if digest in self._hashes:
            existing = next(
                (fact for fact in self.facts if self._hash_text(f"{fact.subject}:{fact.fact}") == digest),
                None,
            )
            if existing is not None:
                return AddFactResult(action="duplicate", fact=existing, invalidated=[])

        active_for_subject = self._active_facts_for_subject(subject)
        has_contradiction = any(_contradicts(old.fact, fact_text) for old in active_for_subject)
        if not has_contradiction:
            for existing in active_for_subject:
                if near_duplicate(existing.fact, fact_text):
                    self._hashes.add(digest)
                    merged = self._merge_near_duplicate(existing, fact_text, when_dt)
                    return AddFactResult(action="merged", fact=merged, invalidated=[])

        invalidated_ids: list[str] = []
        if invalidate_conflicts:
            for old in active_for_subject:
                if _contradicts(old.fact, fact_text):
                    old.invalidate(at=when_dt)
                    invalidated_ids.append(old.fact_id)

        new_fact = TemporalFact(subject=subject.lower(), fact=fact_text, valid_at=when_dt)
        if invalidated_ids:
            new_fact.linked_ids = invalidated_ids

        self.facts.append(new_fact)
        self._hashes.add(digest)
        action = "created" if not invalidated_ids else "superseded"
        return AddFactResult(action=action, fact=new_fact, invalidated=invalidated_ids)

    def episodes_before(self, reference_time: str, limit: int = 10) -> list[Episode]:
        cutoff = _parse_time(reference_time)
        eligible = [episode for episode in self.episodes if _parse_time(episode.reference_time) <= cutoff]
        return eligible[-limit:]

    def compact_episodes(self, keep_recent: int = 5) -> CompactionResult:
        """Summarize older episodes into a recall block, Letta-style.

        Recent episodes stay in-context for retrieval; older ones are folded
        into a single read-only ``recall_summary`` block and moved to
        ``archived_episodes`` so source provenance is preserved without keeping
        every event in the active window.
        """
        if keep_recent < 0:
            raise ValueError("keep_recent must be non-negative")
        if len(self.episodes) <= keep_recent:
            return CompactionResult(summary=None, archived=0, retained=len(self.episodes))

        ordered = sorted(self.episodes, key=lambda ep: _parse_time(ep.reference_time))
        cutoff = len(ordered) - keep_recent
        older, recent = ordered[:cutoff], ordered[cutoff:]

        self.archived_episodes.extend(older)
        self.episodes = recent

        span = f"{older[0].reference_time}..{older[-1].reference_time}"
        bullets = "; ".join(episode.text.strip()[:80] for episode in older)
        summary_value = f"Compacted {len(older)} earlier episodes ({span}): {bullets}"
        summary = self.upsert_block(
            label="recall_summary",
            description="Rolling summary of episodes compacted out of the active window.",
            value=summary_value,
            read_only=True,
        )
        return CompactionResult(summary=summary, archived=len(older), retained=len(recent))

    def active_facts_at(self, as_of: str | None = None) -> list[TemporalFact]:
        moment = utc_now() if as_of is None else _parse_time(as_of)
        return [fact for fact in self.facts if fact.is_active_at(moment)]

    def metadata(self) -> dict[str, int]:
        return {
            "episode_count": len(self.episodes),
            "active_fact_count": len(self.active_facts_at()),
            "block_count": len(self.blocks),
            "graph_edge_count": sum(len(targets) for targets in self.graph.values()),
        }

    def retrieve(
        self,
        query: str,
        as_of: str | None = None,
        limit: int = 8,
        recency_half_life_days: float | None = None,
    ) -> list[str]:
        """Hybrid retrieval over facts, graph edges, episodes and blocks.

        When ``recency_half_life_days`` is set, time-stamped sources (facts and
        episodes) get an exponential recency boost relative to ``as_of`` so that
        fresher, equally-relevant memories rank ahead of stale ones — inspired by
        generative-agents recency weighting. Leaving it ``None`` preserves the
        original purely lexical ranking.
        """
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        moment = utc_now() if as_of is None else _parse_time(as_of)
        results: list[tuple[float, str]] = []

        for fact in self.active_facts_at(as_of):
            score = _score_text(f"{fact.subject} {fact.fact}", terms)
            if score > 0:
                boost = _recency_weight(fact.valid_at, moment, recency_half_life_days)
                results.append((score * boost + 0.2, f"fact[{fact.fact_id}]: {fact.subject} -> {fact.fact}"))

        for source, targets in self.graph.items():
            edge_text = f"{source} {' '.join(sorted(targets))}"
            score = _score_text(edge_text, terms)
            if score > 0:
                results.append((score + 0.1, f"graph: {source} -> {', '.join(sorted(targets))}"))

        for episode in self.episodes_before(as_of or utc_now().isoformat(), limit=5):
            score = _score_text(episode.text, terms)
            if score > 0:
                boost = _recency_weight(_parse_time(episode.reference_time), moment, recency_half_life_days)
                results.append((score * boost, f"episode@{episode.reference_time}: {episode.text}"))

        for block in self.blocks.values():
            score = _score_text(f"{block.label} {block.value}", terms)
            if score > 0:
                results.append((score + 0.15, f"block:{block.label}: {block.value[:120]}"))

        results.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in results[:limit]]


def _parse_time(value: str):
    from datetime import datetime

    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def _recency_weight(event_time, as_of, half_life_days: float | None) -> float:
    """Exponential recency multiplier in ``[~0, 1]`` (1.0 when disabled).

    A memory exactly ``half_life_days`` old keeps half of its lexical score;
    future-dated events are clamped to no boost. Disabled when half-life is None.
    """
    if half_life_days is None:
        return 1.0
    if half_life_days <= 0:
        raise ValueError("recency_half_life_days must be positive")
    age_days = max((as_of - event_time).total_seconds() / 86400.0, 0.0)
    return math.pow(0.5, age_days / half_life_days)


def _score_text(text: str, terms: set[str]) -> float:
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    if not terms:
        return 0.0
    overlap = len(tokens.intersection(terms))
    return overlap / len(terms)


def _contradicts(previous: str, new: str) -> bool:
    previous_tokens = set(previous.lower().split())
    new_tokens = set(new.lower().split())
    if previous.lower() == new.lower():
        return False
    negations = {"not", "no", "never", "without"}
    if previous_tokens.symmetric_difference(new_tokens).intersection(negations):
        return True
    return previous.split()[0:3] == new.split()[0:3]

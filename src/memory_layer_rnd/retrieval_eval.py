"""Fixture-driven retrieval evaluation for comparing ranking strategies."""

from __future__ import annotations

from dataclasses import dataclass, field

from memory_layer_rnd.harness import MemoryHarness
from memory_layer_rnd.retrieval_metrics import RetrievalMetrics, parse_retrieved_keys, precision_recall_f1
from memory_layer_rnd.scopes import SessionScope


@dataclass(frozen=True)
class FactFixture:
    key: str
    subject: str
    fact: str
    reference_time: str


@dataclass(frozen=True)
class EpisodeFixture:
    key: str
    text: str
    reference_time: str


@dataclass(frozen=True)
class BlockFixture:
    key: str
    label: str
    description: str
    value: str


@dataclass(frozen=True)
class FactLinkFixture:
    source_key: str
    target_key: str
    relation: str = "related"


@dataclass(frozen=True)
class RetrievalEvalCase:
    name: str
    query: str
    relevant_keys: frozenset[str]
    facts: tuple[FactFixture, ...] = ()
    episodes: tuple[EpisodeFixture, ...] = ()
    blocks: tuple[BlockFixture, ...] = ()
    links: tuple[FactLinkFixture, ...] = ()
    as_of: str | None = None


@dataclass(frozen=True)
class RetrievalStrategy:
    name: str
    recency_half_life_days: float | None = None
    limit: int = 8


@dataclass(frozen=True)
class CaseEvalResult:
    case_name: str
    strategy: str
    metrics: RetrievalMetrics


@dataclass(frozen=True)
class StrategyComparison:
    strategy: str
    mean_precision: float
    mean_recall: float
    mean_f1: float
    case_results: tuple[CaseEvalResult, ...]


@dataclass
class EvalHarnessState:
    harness: MemoryHarness
    fact_id_to_key: dict[str, str] = field(default_factory=dict)
    episode_text_to_key: dict[str, str] = field(default_factory=dict)
    block_label_to_key: dict[str, str] = field(default_factory=dict)


def bootstrap_eval_harness(
    case: RetrievalEvalCase,
    *,
    scope: SessionScope | None = None,
    decay_half_life_days: float | None = None,
) -> EvalHarnessState:
    """Populate a harness from a fixture case and record stable key maps."""
    harness = MemoryHarness(
        scope=scope or SessionScope(user_id="eval"),
        decay_half_life_days=decay_half_life_days,
    )
    state = EvalHarnessState(harness=harness)

    for block in case.blocks:
        harness.upsert_block(block.label, block.description, block.value)
        state.block_label_to_key[block.label] = block.key

    for episode in case.episodes:
        harness.remember_episode(episode.text, reference_time=episode.reference_time)
        state.episode_text_to_key[episode.text] = episode.key

    key_to_fact_id: dict[str, str] = {}
    for fact in case.facts:
        result = harness.add_fact(fact.subject, fact.fact, reference_time=fact.reference_time)
        key_to_fact_id[fact.key] = result.fact.fact_id
        state.fact_id_to_key[result.fact.fact_id] = fact.key

    for link in case.links:
        source_id = key_to_fact_id[link.source_key]
        target_id = key_to_fact_id[link.target_key]
        harness.link_facts(source_id, target_id, relation=link.relation)

    return state


def evaluate_case(
    case: RetrievalEvalCase,
    strategy: RetrievalStrategy,
    *,
    scope: SessionScope | None = None,
    decay_half_life_days: float | None = None,
) -> CaseEvalResult:
    """Run one eval case under a retrieval strategy and return metrics."""
    state = bootstrap_eval_harness(
        case,
        scope=scope,
        decay_half_life_days=decay_half_life_days,
    )
    lines = state.harness.retrieve(
        case.query,
        as_of=case.as_of,
        limit=strategy.limit,
        recency_half_life_days=strategy.recency_half_life_days,
    )
    retrieved = parse_retrieved_keys(
        lines,
        fact_id_to_key=state.fact_id_to_key,
        episode_text_to_key=state.episode_text_to_key,
        block_label_to_key=state.block_label_to_key,
    )
    metrics = precision_recall_f1(retrieved, set(case.relevant_keys))
    return CaseEvalResult(case_name=case.name, strategy=strategy.name, metrics=metrics)


def compare_strategies(
    cases: list[RetrievalEvalCase],
    strategies: list[RetrievalStrategy],
    *,
    scope: SessionScope | None = None,
    decay_half_life_days: float | None = None,
) -> list[StrategyComparison]:
    """Evaluate every case under each strategy and aggregate mean metrics."""
    comparisons: list[StrategyComparison] = []
    for strategy in strategies:
        case_results = tuple(
            evaluate_case(
                case,
                strategy,
                scope=scope,
                decay_half_life_days=decay_half_life_days,
            )
            for case in cases
        )
        if case_results:
            mean_precision = sum(item.metrics.precision for item in case_results) / len(case_results)
            mean_recall = sum(item.metrics.recall for item in case_results) / len(case_results)
            mean_f1 = sum(item.metrics.f1 for item in case_results) / len(case_results)
        else:
            mean_precision = mean_recall = mean_f1 = 0.0
        comparisons.append(
            StrategyComparison(
                strategy=strategy.name,
                mean_precision=mean_precision,
                mean_recall=mean_recall,
                mean_f1=mean_f1,
                case_results=case_results,
            )
        )
    return comparisons


RETRIEVAL_EVAL_FIXTURES: tuple[RetrievalEvalCase, ...] = (
    RetrievalEvalCase(
        name="lexical_focus",
        query="temporal memory focus",
        relevant_keys=frozenset({"fresh_focus"}),
        facts=(
            FactFixture(
                key="stale_focus",
                subject="focus",
                fact="vector only memory research",
                reference_time="2026-01-01T00:00:00+00:00",
            ),
            FactFixture(
                key="fresh_focus",
                subject="focus",
                fact="temporal memory focus with invalidation",
                reference_time="2026-06-15T09:00:00+00:00",
            ),
            FactFixture(
                key="distractor",
                subject="infra",
                fact="kubernetes evaluation cluster",
                reference_time="2026-06-01T10:00:00+00:00",
            ),
        ),
        as_of="2026-06-20T00:00:00+00:00",
    ),
    RetrievalEvalCase(
        name="recency_ranking",
        query="graph memory retrieval",
        relevant_keys=frozenset({"fresh_alpha"}),
        facts=(
            FactFixture(
                key="stale_alpha",
                subject="alpha",
                fact="graph memory retrieval",
                reference_time="2026-01-01T00:00:00+00:00",
            ),
            FactFixture(
                key="fresh_alpha",
                subject="beta",
                fact="graph memory retrieval",
                reference_time="2026-06-01T00:00:00+00:00",
            ),
        ),
        as_of="2026-06-10T00:00:00+00:00",
    ),
    RetrievalEvalCase(
        name="graph_neighbor",
        query="memory layer research",
        relevant_keys=frozenset({"anchor", "neighbor"}),
        facts=(
            FactFixture(
                key="anchor",
                subject="project",
                fact="memory layer research",
                reference_time="2026-06-01T10:00:00+00:00",
            ),
            FactFixture(
                key="neighbor",
                subject="infra",
                fact="kubernetes cluster east",
                reference_time="2026-06-01T10:05:00+00:00",
            ),
        ),
        links=(FactLinkFixture(source_key="anchor", target_key="neighbor", relation="deploys_on"),),
        as_of="2026-06-15T00:00:00+00:00",
    ),
    RetrievalEvalCase(
        name="multi_source",
        query="graph memory",
        relevant_keys=frozenset({"topic_fact", "prefs_block", "discussion_episode"}),
        facts=(
            FactFixture(
                key="topic_fact",
                subject="topic",
                fact="graph memory retrieval patterns",
                reference_time="2026-06-01T10:00:00+00:00",
            ),
        ),
        blocks=(
            BlockFixture(
                key="prefs_block",
                label="human",
                description="preferences",
                value="likes graph memory systems",
            ),
        ),
        episodes=(
            EpisodeFixture(
                key="discussion_episode",
                text="Discussed graph memory patterns in the planning session",
                reference_time="2026-06-01T10:00:00+00:00",
            ),
        ),
        as_of="2026-06-15T12:00:00+00:00",
    ),
)

DEFAULT_STRATEGIES: tuple[RetrievalStrategy, ...] = (
    RetrievalStrategy(name="lexical", recency_half_life_days=None, limit=8),
    RetrievalStrategy(name="recency_30d", recency_half_life_days=30.0, limit=8),
    RetrievalStrategy(name="lexical_top1", recency_half_life_days=None, limit=1),
    RetrievalStrategy(name="recency_30d_top1", recency_half_life_days=30.0, limit=1),
)

import pytest

from memory_layer_rnd.retrieval_eval import (
    DEFAULT_STRATEGIES,
    RETRIEVAL_EVAL_FIXTURES,
    FactFixture,
    FactLinkFixture,
    RetrievalEvalCase,
    RetrievalStrategy,
    bootstrap_eval_harness,
    compare_strategies,
    evaluate_case,
)
from memory_layer_rnd.retrieval_metrics import (
    parse_retrieved_keys,
    precision_recall_f1,
)


def test_precision_recall_f1_perfect_match() -> None:
    metrics = precision_recall_f1({"a", "b"}, {"a", "b"})

    assert metrics.precision == pytest.approx(1.0)
    assert metrics.recall == pytest.approx(1.0)
    assert metrics.f1 == pytest.approx(1.0)
    assert metrics.true_positives == 2


def test_precision_recall_f1_partial_overlap() -> None:
    metrics = precision_recall_f1({"a", "b", "c"}, {"a", "d"})

    assert metrics.precision == pytest.approx(1 / 3)
    assert metrics.recall == pytest.approx(0.5)
    assert metrics.true_positives == 1


def test_precision_recall_f1_empty_sets() -> None:
    metrics = precision_recall_f1(set(), set())

    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0


def test_parse_retrieved_keys_maps_fact_episode_and_block_lines() -> None:
    lines = [
        "fact[abc12345]: focus -> temporal memory focus",
        "related[1] via uses: stack -> python fastapi (id=def67890)",
        "episode@2026-06-01T10:00:00+00:00: Discussed graph memory patterns",
        "block:human: likes graph memory systems",
    ]
    keys = parse_retrieved_keys(
        lines,
        fact_id_to_key={"abc12345": "topic", "def67890": "stack"},
        episode_text_to_key={"Discussed graph memory patterns": "episode"},
        block_label_to_key={"human": "prefs"},
    )

    assert keys == {"topic", "stack", "episode", "prefs"}


def test_bootstrap_eval_harness_records_fixture_keys() -> None:
    case = next(item for item in RETRIEVAL_EVAL_FIXTURES if item.name == "graph_neighbor")
    state = bootstrap_eval_harness(case)

    assert set(state.fact_id_to_key.values()) == {"anchor", "neighbor"}
    assert state.harness.metadata()["fact_edge_count"] == 1


def test_evaluate_case_lexical_focus_finds_relevant_fact() -> None:
    case = next(item for item in RETRIEVAL_EVAL_FIXTURES if item.name == "lexical_focus")
    strategy = RetrievalStrategy(name="lexical", recency_half_life_days=None, limit=8)

    result = evaluate_case(case, strategy)

    assert "fresh_focus" in result.metrics.retrieved_keys
    assert result.metrics.recall == pytest.approx(1.0)


def test_recency_strategy_promotes_fresh_fact_at_top1() -> None:
    case = next(item for item in RETRIEVAL_EVAL_FIXTURES if item.name == "recency_ranking")
    lexical = RetrievalStrategy(name="lexical_top1", recency_half_life_days=None, limit=1)
    recency = RetrievalStrategy(name="recency_top1", recency_half_life_days=30.0, limit=1)

    lexical_result = evaluate_case(case, lexical)
    recency_result = evaluate_case(case, recency)

    assert lexical_result.metrics.retrieved_keys == frozenset({"stale_alpha"})
    assert recency_result.metrics.retrieved_keys == frozenset({"fresh_alpha"})
    assert recency_result.metrics.precision > lexical_result.metrics.precision


def test_graph_neighbor_case_recalls_linked_fact() -> None:
    case = next(item for item in RETRIEVAL_EVAL_FIXTURES if item.name == "graph_neighbor")
    strategy = RetrievalStrategy(name="lexical", recency_half_life_days=None, limit=8)

    result = evaluate_case(case, strategy)

    assert result.metrics.relevant_keys == frozenset({"anchor", "neighbor"})
    assert result.metrics.retrieved_keys == result.metrics.relevant_keys
    assert result.metrics.recall == pytest.approx(1.0)


def test_multi_source_fixture_hits_facts_blocks_and_episodes() -> None:
    case = next(item for item in RETRIEVAL_EVAL_FIXTURES if item.name == "multi_source")
    strategy = RetrievalStrategy(name="lexical", recency_half_life_days=None, limit=8)

    result = evaluate_case(case, strategy)

    assert result.metrics.retrieved_keys == frozenset(
        {"topic_fact", "prefs_block", "discussion_episode"}
    )


def test_compare_strategies_ranks_recency_top1_ahead_of_lexical_top1() -> None:
    comparisons = compare_strategies(
        list(RETRIEVAL_EVAL_FIXTURES),
        [
            RetrievalStrategy(name="lexical_top1", recency_half_life_days=None, limit=1),
            RetrievalStrategy(name="recency_30d_top1", recency_half_life_days=30.0, limit=1),
        ],
    )
    by_name = {item.strategy: item for item in comparisons}

    assert by_name["recency_30d_top1"].mean_f1 > by_name["lexical_top1"].mean_f1
    assert len(by_name["recency_30d_top1"].case_results) == len(RETRIEVAL_EVAL_FIXTURES)


def test_default_strategies_cover_lexical_and_recency_modes() -> None:
    names = {strategy.name for strategy in DEFAULT_STRATEGIES}

    assert "lexical" in names
    assert "recency_30d" in names
    assert "lexical_top1" in names
    assert "recency_30d_top1" in names


def test_evaluate_case_rejects_unknown_fixture_keys_in_links() -> None:
    case = RetrievalEvalCase(
        name="broken_link",
        query="memory",
        relevant_keys=frozenset({"anchor"}),
        facts=(
            FactFixture(
                key="anchor",
                subject="project",
                fact="memory layer research",
                reference_time="2026-06-01T10:00:00+00:00",
            ),
        ),
        links=(
            FactLinkFixture(
                source_key="anchor",
                target_key="missing",
            ),
        ),
    )

    with pytest.raises(KeyError):
        evaluate_case(case, DEFAULT_STRATEGIES[0])

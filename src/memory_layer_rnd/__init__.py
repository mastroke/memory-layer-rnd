"""Memory-layer research primitives for AI agents."""

from memory_layer_rnd.blocks import CoreBlock
from memory_layer_rnd.decay import decay_weight_for_age, temporal_decay_weight
from memory_layer_rnd.graph import FactEdge, FactGraph
from memory_layer_rnd.harness import AddFactResult, CompactionResult, Episode, MemoryHarness
from memory_layer_rnd.memory import MemoryEvent, MemoryStore
from memory_layer_rnd.resolver import ConflictStrategy, ContradictionOutcome, resolve_contradiction
from memory_layer_rnd.retrieval_eval import (
    DEFAULT_STRATEGIES,
    RETRIEVAL_EVAL_FIXTURES,
    CaseEvalResult,
    EvalHarnessState,
    RetrievalEvalCase,
    RetrievalStrategy,
    StrategyComparison,
    bootstrap_eval_harness,
    compare_strategies,
    evaluate_case,
)
from memory_layer_rnd.retrieval_metrics import RetrievalMetrics, parse_retrieved_keys, precision_recall_f1
from memory_layer_rnd.scopes import SessionScope
from memory_layer_rnd.temporal import TemporalFact

__all__ = [
    "AddFactResult",
    "CaseEvalResult",
    "CompactionResult",
    "ConflictStrategy",
    "ContradictionOutcome",
    "CoreBlock",
    "DEFAULT_STRATEGIES",
    "Episode",
    "EvalHarnessState",
    "FactEdge",
    "FactGraph",
    "MemoryEvent",
    "MemoryHarness",
    "MemoryStore",
    "RETRIEVAL_EVAL_FIXTURES",
    "RetrievalEvalCase",
    "RetrievalMetrics",
    "RetrievalStrategy",
    "SessionScope",
    "StrategyComparison",
    "TemporalFact",
    "bootstrap_eval_harness",
    "compare_strategies",
    "decay_weight_for_age",
    "evaluate_case",
    "parse_retrieved_keys",
    "precision_recall_f1",
    "resolve_contradiction",
    "temporal_decay_weight",
]

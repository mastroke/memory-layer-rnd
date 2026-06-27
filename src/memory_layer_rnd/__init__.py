"""Memory-layer research primitives for AI agents."""

from memory_layer_rnd.blocks import CoreBlock
from memory_layer_rnd.decay import decay_weight_for_age, temporal_decay_weight
from memory_layer_rnd.graph import FactEdge, FactGraph
from memory_layer_rnd.harness import AddFactResult, CompactionResult, Episode, MemoryHarness
from memory_layer_rnd.memory import MemoryEvent, MemoryStore
from memory_layer_rnd.resolver import ConflictStrategy, ContradictionOutcome, resolve_contradiction
from memory_layer_rnd.scopes import SessionScope
from memory_layer_rnd.temporal import TemporalFact

__all__ = [
    "AddFactResult",
    "CompactionResult",
    "ConflictStrategy",
    "ContradictionOutcome",
    "CoreBlock",
    "Episode",
    "FactEdge",
    "FactGraph",
    "MemoryEvent",
    "MemoryHarness",
    "MemoryStore",
    "SessionScope",
    "TemporalFact",
    "decay_weight_for_age",
    "resolve_contradiction",
    "temporal_decay_weight",
]

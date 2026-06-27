"""Precision and recall helpers for ranked retrieval evaluation."""

from __future__ import annotations

import re
from dataclasses import dataclass

_FACT_ID_RE = re.compile(r"^fact\[([^\]]+)\]:")
_RELATED_ID_RE = re.compile(r"\(id=([^)]+)\)\s*$")
_BLOCK_LABEL_RE = re.compile(r"^block:([^:]+):")


@dataclass(frozen=True)
class RetrievalMetrics:
    """Set-based precision, recall and F1 for a single query."""

    precision: float
    recall: float
    f1: float
    retrieved_keys: frozenset[str]
    relevant_keys: frozenset[str]

    @property
    def true_positives(self) -> int:
        return len(self.retrieved_keys.intersection(self.relevant_keys))


def precision_recall_f1(retrieved: set[str], relevant: set[str]) -> RetrievalMetrics:
    """Compute set precision, recall and F1 over retrieved and relevant keys."""
    if not retrieved and not relevant:
        return RetrievalMetrics(
            precision=0.0,
            recall=0.0,
            f1=0.0,
            retrieved_keys=frozenset(),
            relevant_keys=frozenset(relevant),
        )

    hits = retrieved.intersection(relevant)
    precision = len(hits) / len(retrieved) if retrieved else 0.0
    recall = len(hits) / len(relevant) if relevant else 0.0
    if precision + recall == 0.0:
        f1 = 0.0
    else:
        f1 = 2.0 * precision * recall / (precision + recall)

    return RetrievalMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        retrieved_keys=frozenset(retrieved),
        relevant_keys=frozenset(relevant),
    )


def parse_retrieved_keys(
    lines: list[str],
    *,
    fact_id_to_key: dict[str, str],
    episode_text_to_key: dict[str, str],
    block_label_to_key: dict[str, str],
) -> set[str]:
    """Map ``retrieve()`` result lines back to fixture keys."""
    keys: set[str] = set()
    for line in lines:
        key = _key_from_line(
            line,
            fact_id_to_key=fact_id_to_key,
            episode_text_to_key=episode_text_to_key,
            block_label_to_key=block_label_to_key,
        )
        if key is not None:
            keys.add(key)
    return keys


def _key_from_line(
    line: str,
    *,
    fact_id_to_key: dict[str, str],
    episode_text_to_key: dict[str, str],
    block_label_to_key: dict[str, str],
) -> str | None:
    fact_match = _FACT_ID_RE.match(line)
    if fact_match is not None:
        return fact_id_to_key.get(fact_match.group(1))

    related_match = _RELATED_ID_RE.search(line)
    if related_match is not None:
        return fact_id_to_key.get(related_match.group(1))

    if line.startswith("episode@"):
        for text, key in episode_text_to_key.items():
            if text in line:
                return key
        return None

    block_match = _BLOCK_LABEL_RE.match(line)
    if block_match is not None:
        return block_label_to_key.get(block_match.group(1))

    return None

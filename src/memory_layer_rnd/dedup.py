"""Lexical near-duplicate detection for the fact write path."""

from __future__ import annotations

import re

DEFAULT_NEAR_DUPLICATE_THRESHOLD = 0.8


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def overlap_coefficient(left: str, right: str) -> float:
    """Share of the smaller token set covered by the intersection."""
    left_tokens = tokenize(left)
    right_tokens = tokenize(right)
    if not left_tokens or not right_tokens:
        return 0.0
    shared = len(left_tokens & right_tokens)
    return shared / min(len(left_tokens), len(right_tokens))


def near_duplicate(
    left: str,
    right: str,
    *,
    threshold: float = DEFAULT_NEAR_DUPLICATE_THRESHOLD,
) -> bool:
    """Return True when two fact texts are near-identical under token overlap."""
    if left.strip().lower() == right.strip().lower():
        return True
    return overlap_coefficient(left, right) >= threshold

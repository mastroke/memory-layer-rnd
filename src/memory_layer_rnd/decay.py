"""Exponential time-decay helpers for memory weight and invalidation."""

from __future__ import annotations

import math
from datetime import datetime


def age_days(event_time: datetime, as_of: datetime) -> float:
    """Non-negative age of ``event_time`` relative to ``as_of`` in days."""
    return max((as_of - event_time).total_seconds() / 86400.0, 0.0)


def decay_weight_for_age(age_days: float, half_life_days: float) -> float:
    """Return decay weight in ``(0, 1]`` for a given age and half-life.

    Weight is ``1.0`` at age zero and halves every ``half_life_days``.
    """
    return math.pow(0.5, age_days / half_life_days)


def temporal_decay_weight(
    event_time: datetime,
    as_of: datetime,
    half_life_days: float | None,
) -> float:
    """Exponential decay multiplier for an event timestamp relative to ``as_of``.

    Returns ``1.0`` when decay is disabled (``half_life_days`` is ``None``).
    """
    if half_life_days is None:
        return 1.0
    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive")
    return decay_weight_for_age(age_days(event_time, as_of), half_life_days)

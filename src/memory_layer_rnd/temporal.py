from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TemporalFact:
    """Inspired by Graphiti valid_at / invalid_at semantics."""

    subject: str
    fact: str
    valid_at: datetime
    invalid_at: datetime | None = None
    expired_at: datetime | None = None
    confidence: float = 1.0
    linked_ids: list[str] = field(default_factory=list)
    fact_id: str = field(default_factory=lambda: uuid4().hex[:8])

    @property
    def is_active(self) -> bool:
        return self.invalid_at is None

    def is_active_at(self, as_of: datetime) -> bool:
        if self.valid_at > as_of:
            return False
        if self.invalid_at is not None and self.invalid_at <= as_of:
            return False
        return True

    def invalidate(self, at: datetime, expired_at: datetime | None = None) -> None:
        self.invalid_at = at
        self.expired_at = expired_at or utc_now()

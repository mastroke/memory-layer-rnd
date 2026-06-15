from dataclasses import dataclass


@dataclass(frozen=True)
class SessionScope:
    """Inspired by Mem0 user/agent/run scoping."""

    user_id: str | None = None
    agent_id: str | None = None
    run_id: str | None = None

    def __post_init__(self) -> None:
        if not any((self.user_id, self.agent_id, self.run_id)):
            raise ValueError("At least one scope identifier is required")

    @property
    def key(self) -> str:
        return "|".join(
            [
                f"user:{self.user_id or '*'}",
                f"agent:{self.agent_id or '*'}",
                f"run:{self.run_id or '*'}",
            ]
        )

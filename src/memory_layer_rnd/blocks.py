from dataclasses import dataclass


@dataclass
class CoreBlock:
    """Inspired by Letta labeled core memory blocks."""

    label: str
    description: str
    value: str = ""
    char_limit: int = 2000
    read_only: bool = False

    def render(self) -> str:
        clipped = self.value[: self.char_limit]
        return (
            f'<block label="{self.label}" read_only="{self.read_only}">'
            f"<description>{self.description}</description>"
            f"<value>{clipped}</value>"
            f"</block>"
        )

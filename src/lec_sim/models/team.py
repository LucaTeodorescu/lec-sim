"""Team model."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Team:
    """Represents a team in the tournament."""

    name: str
    short_name: str  # e.g., "FNC", "G2"
    id: UUID = field(default_factory=uuid4)
    is_erl: bool = False  # True for Los Ratones, Karmine Corp Blue

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Team):
            return self.id == other.id
        return False

    def __repr__(self) -> str:
        return f"Team({self.short_name})"

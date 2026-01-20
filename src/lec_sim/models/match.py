"""Match and MatchResult models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from lec_sim.models.team import Team


class MatchFormat(Enum):
    """Match format (best of N)."""

    BO1 = 1
    BO3 = 3
    BO5 = 5

    @property
    def games_to_win(self) -> int:
        """Number of games needed to win the series."""
        return (self.value + 1) // 2


@dataclass
class MatchResult:
    """Result of a completed match."""

    winner: Team
    loser: Team
    winner_score: int  # Games won (1 for Bo1, up to 3 for Bo5)
    loser_score: int

    @property
    def is_sweep(self) -> bool:
        """Check if the winner swept (opponent won 0 games)."""
        return self.loser_score == 0


@dataclass
class Match:
    """Represents a scheduled or completed match."""

    team_a: Team
    team_b: Team
    format: MatchFormat = MatchFormat.BO1
    stage: str = "round_robin"  # "round_robin", "upper_r1", "lower_final", etc.
    week: Optional[int] = None
    match_day: Optional[int] = None
    result: Optional[MatchResult] = None
    id: UUID = field(default_factory=uuid4)

    @property
    def is_completed(self) -> bool:
        """Check if the match has been played."""
        return self.result is not None

    def get_opponent(self, team: Team) -> Team:
        """Get the opponent of the given team in this match."""
        if team == self.team_a:
            return self.team_b
        elif team == self.team_b:
            return self.team_a
        raise ValueError(f"{team} is not in this match")

    def __repr__(self) -> str:
        if self.result:
            return f"Match({self.team_a.short_name} vs {self.team_b.short_name}: {self.result.winner.short_name} wins)"
        return f"Match({self.team_a.short_name} vs {self.team_b.short_name})"

"""Standing models for tracking team records."""

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from lec_sim.models.team import Team


@dataclass
class TeamStanding:
    """Standing for a single team."""

    team: Team
    wins: int = 0
    losses: int = 0
    # head_to_head: opponent_id -> (wins against them, losses against them)
    head_to_head: dict[UUID, tuple[int, int]] = field(default_factory=dict)

    @property
    def games_played(self) -> int:
        """Total games played."""
        return self.wins + self.losses

    @property
    def win_rate(self) -> float:
        """Win rate as a decimal."""
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played

    def record_win(self, opponent_id: UUID) -> None:
        """Record a win against an opponent."""
        self.wins += 1
        w, l = self.head_to_head.get(opponent_id, (0, 0))
        self.head_to_head[opponent_id] = (w + 1, l)

    def record_loss(self, opponent_id: UUID) -> None:
        """Record a loss against an opponent."""
        self.losses += 1
        w, l = self.head_to_head.get(opponent_id, (0, 0))
        self.head_to_head[opponent_id] = (w, l + 1)

    def get_h2h_record(self, opponent_id: UUID) -> tuple[int, int]:
        """Get head-to-head record against an opponent."""
        return self.head_to_head.get(opponent_id, (0, 0))

    def copy(self) -> "TeamStanding":
        """Create a deep copy of this standing."""
        return TeamStanding(
            team=self.team,
            wins=self.wins,
            losses=self.losses,
            head_to_head=dict(self.head_to_head),
        )

    def __repr__(self) -> str:
        return f"Standing({self.team.short_name}: {self.wins}-{self.losses})"


@dataclass
class Standings:
    """Collection of all team standings."""

    standings: dict[UUID, TeamStanding] = field(default_factory=dict)

    def get(self, team_id: UUID) -> Optional[TeamStanding]:
        """Get standing for a team by ID."""
        return self.standings.get(team_id)

    def get_by_team(self, team: Team) -> Optional[TeamStanding]:
        """Get standing for a team."""
        return self.standings.get(team.id)

    def add_team(self, team: Team) -> TeamStanding:
        """Add a team to standings (creates empty record)."""
        standing = TeamStanding(team=team)
        self.standings[team.id] = standing
        return standing

    def record_match_result(self, winner: Team, loser: Team) -> None:
        """Record a match result in standings."""
        winner_standing = self.standings.get(winner.id)
        loser_standing = self.standings.get(loser.id)

        if winner_standing is None or loser_standing is None:
            raise ValueError("Both teams must be in standings")

        winner_standing.record_win(loser.id)
        loser_standing.record_loss(winner.id)

    def get_ordered(self) -> list[TeamStanding]:
        """Return standings ordered by wins (desc), then losses (asc)."""
        return sorted(
            self.standings.values(),
            key=lambda s: (-s.wins, s.losses),
        )

    def get_teams_with_wins(self, wins: int) -> list[TeamStanding]:
        """Get all teams with exactly N wins."""
        return [s for s in self.standings.values() if s.wins == wins]

    def copy(self) -> "Standings":
        """Create a deep copy of standings."""
        new_standings = Standings()
        for team_id, standing in self.standings.items():
            new_standings.standings[team_id] = standing.copy()
        return new_standings

    def __len__(self) -> int:
        return len(self.standings)

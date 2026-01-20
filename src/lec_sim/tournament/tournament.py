"""Main tournament orchestration."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
import random

from lec_sim.models.team import Team
from lec_sim.models.match import Match, MatchResult
from lec_sim.models.standing import Standings, TeamStanding
from lec_sim.tournament.round_robin import generate_round_robin_schedule
from lec_sim.tournament.playoffs import PlayoffBracket, BracketPosition
from lec_sim.tiebreaker.resolver import TiebreakerChain


@dataclass
class Tournament:
    """
    Main tournament orchestration class.

    Supports loading from a snapshot and simulating forward.
    """

    teams: list[Team]
    standings: Standings = field(default_factory=Standings)
    round_robin_matches: list[Match] = field(default_factory=list)
    playoff_bracket: Optional[PlayoffBracket] = None

    # Track which matches have been played
    _completed_match_ids: set = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize standings if empty."""
        if len(self.standings) == 0:
            for team in self.teams:
                self.standings.add_team(team)

    @classmethod
    def create_new(cls, teams: list[Team]) -> "Tournament":
        """Create a new tournament with full round-robin schedule."""
        tournament = cls(teams=teams)
        tournament.round_robin_matches = generate_round_robin_schedule(teams)
        return tournament

    def get_remaining_round_robin_matches(self) -> list[Match]:
        """Get all round-robin matches that haven't been played."""
        return [m for m in self.round_robin_matches if not m.is_completed]

    def get_completed_round_robin_matches(self) -> list[Match]:
        """Get all round-robin matches that have been played."""
        return [m for m in self.round_robin_matches if m.is_completed]

    def record_round_robin_result(self, match: Match, result: MatchResult) -> None:
        """Record a round-robin match result."""
        match.result = result
        self._completed_match_ids.add(match.id)
        self.standings.record_match_result(result.winner, result.loser)

    def resolve_standings(
        self, rng: Optional[random.Random] = None
    ) -> list[TeamStanding]:
        """
        Get final standings with tiebreakers resolved.

        Returns teams ordered from 1st to 12th (or however many teams).
        """
        # Group teams by win count
        by_wins: dict[int, list[TeamStanding]] = defaultdict(list)
        for standing in self.standings.standings.values():
            by_wins[standing.wins].append(standing)

        # Resolve ties within each win group
        tiebreaker_chain = TiebreakerChain(rng=rng)
        final_order: list[TeamStanding] = []

        for wins in sorted(by_wins.keys(), reverse=True):
            group = by_wins[wins]
            if len(group) == 1:
                final_order.extend(group)
            else:
                result = tiebreaker_chain.resolve(group, self.standings)
                final_order.extend(result.ordered_teams)

        return final_order

    def create_playoff_bracket(
        self, seeded_standings: list[TeamStanding]
    ) -> PlayoffBracket:
        """Create playoff bracket from top 8 teams."""
        if len(seeded_standings) < 8:
            raise ValueError("Need at least 8 teams for playoffs")

        bracket = PlayoffBracket()
        bracket.seed_teams([s.team for s in seeded_standings[:8]])
        self.playoff_bracket = bracket
        return bracket

    def copy(self) -> "Tournament":
        """Create a deep copy of the tournament for simulation."""
        new_tournament = Tournament(
            teams=self.teams,  # Teams are immutable, can share
            standings=self.standings.copy(),
            round_robin_matches=[],  # Will rebuild
        )

        # Deep copy matches
        for match in self.round_robin_matches:
            new_match = Match(
                team_a=match.team_a,
                team_b=match.team_b,
                format=match.format,
                stage=match.stage,
                week=match.week,
                match_day=match.match_day,
                result=match.result,  # MatchResult is immutable
                id=match.id,
            )
            new_tournament.round_robin_matches.append(new_match)

        new_tournament._completed_match_ids = set(self._completed_match_ids)
        return new_tournament

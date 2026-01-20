"""Tiebreaker resolution system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
import random

from lec_sim.models.standing import TeamStanding, Standings


class TiebreakerMethod(Enum):
    """Types of tiebreaker methods."""

    HEAD_TO_HEAD = auto()
    STRENGTH_OF_VICTORY = auto()
    COINFLIP = auto()


@dataclass
class TiebreakerResult:
    """Result of applying a tiebreaker."""

    resolved: bool
    method_used: Optional[TiebreakerMethod]
    ordered_teams: list[TeamStanding]
    notes: str = ""


class TiebreakerRule(ABC):
    """Abstract base for tiebreaker rules."""

    @abstractmethod
    def resolve(
        self,
        tied_teams: list[TeamStanding],
        all_standings: Standings,
    ) -> TiebreakerResult:
        """Attempt to resolve tie between teams."""
        pass


class HeadToHeadTiebreaker(TiebreakerRule):
    """Resolve ties based on head-to-head record."""

    def resolve(
        self,
        tied_teams: list[TeamStanding],
        all_standings: Standings,
    ) -> TiebreakerResult:
        if len(tied_teams) == 2:
            return self._resolve_two_way(tied_teams)
        return self._resolve_multi_way(tied_teams)

    def _resolve_two_way(self, teams: list[TeamStanding]) -> TiebreakerResult:
        """Resolve a two-way tie using direct H2H."""
        t1, t2 = teams
        h2h_1 = t1.get_h2h_record(t2.team.id)
        h2h_2 = t2.get_h2h_record(t1.team.id)

        if h2h_1[0] > h2h_2[0]:
            return TiebreakerResult(
                True, TiebreakerMethod.HEAD_TO_HEAD, [t1, t2], "H2H wins"
            )
        elif h2h_2[0] > h2h_1[0]:
            return TiebreakerResult(
                True, TiebreakerMethod.HEAD_TO_HEAD, [t2, t1], "H2H wins"
            )

        return TiebreakerResult(False, None, teams, "H2H tied")

    def _resolve_multi_way(self, teams: list[TeamStanding]) -> TiebreakerResult:
        """
        For 3+ way ties, calculate wins/losses among tied teams only.

        Teams are separated by their internal record (wins - losses among tied teams).
        """
        # Calculate internal records (wins among tied teams only)
        team_ids = {t.team.id for t in teams}
        internal_records: dict[str, tuple[int, int, int]] = {}  # (wins, losses, diff)

        for t in teams:
            wins = sum(
                t.get_h2h_record(other_id)[0]
                for other_id in team_ids
                if other_id != t.team.id
            )
            losses = sum(
                t.get_h2h_record(other_id)[1]
                for other_id in team_ids
                if other_id != t.team.id
            )
            internal_records[str(t.team.id)] = (wins, losses, wins - losses)

        # Sort by win differential
        sorted_teams = sorted(
            teams,
            key=lambda t: internal_records[str(t.team.id)][2],
            reverse=True,
        )

        # Check if fully resolved (all different differentials)
        diffs = [internal_records[str(t.team.id)][2] for t in sorted_teams]
        if len(set(diffs)) == len(diffs):
            return TiebreakerResult(
                True, TiebreakerMethod.HEAD_TO_HEAD, sorted_teams, "Multi-way H2H"
            )

        return TiebreakerResult(
            False, None, sorted_teams, "Multi-way H2H partially resolved"
        )


class StrengthOfVictoryTiebreaker(TiebreakerRule):
    """
    Strength of Victory (SoV): Sum of opponent wins for each victory.

    Higher SoV = beat stronger opponents = ranked higher.
    """

    def resolve(
        self,
        tied_teams: list[TeamStanding],
        all_standings: Standings,
    ) -> TiebreakerResult:
        sov_scores: dict[str, int] = {}

        for team in tied_teams:
            sov = 0
            for opp_id, (wins_vs, _) in team.head_to_head.items():
                if wins_vs > 0:  # We beat this opponent
                    opp_standing = all_standings.get(opp_id)
                    if opp_standing:
                        # Add opponent's total wins * times we beat them
                        sov += opp_standing.wins * wins_vs
            sov_scores[str(team.team.id)] = sov

        sorted_teams = sorted(
            tied_teams,
            key=lambda t: sov_scores[str(t.team.id)],
            reverse=True,
        )

        # Check if resolved
        scores = [sov_scores[str(t.team.id)] for t in sorted_teams]
        if len(set(scores)) == len(scores):
            return TiebreakerResult(
                True, TiebreakerMethod.STRENGTH_OF_VICTORY, sorted_teams, "SoV"
            )

        return TiebreakerResult(False, None, sorted_teams, "SoV tied")


class CoinflipTiebreaker(TiebreakerRule):
    """Last resort: random tiebreaker."""

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()

    def resolve(
        self,
        tied_teams: list[TeamStanding],
        all_standings: Standings,
    ) -> TiebreakerResult:
        shuffled = list(tied_teams)
        self.rng.shuffle(shuffled)
        return TiebreakerResult(
            True, TiebreakerMethod.COINFLIP, shuffled, "Random tiebreaker"
        )


class TiebreakerChain:
    """
    Apply tiebreakers in order until resolved.

    Default LEC order: H2H -> SoV -> Coinflip
    """

    def __init__(
        self, rules: Optional[list[TiebreakerRule]] = None, rng: Optional[random.Random] = None
    ):
        self.rules = rules or [
            HeadToHeadTiebreaker(),
            StrengthOfVictoryTiebreaker(),
            CoinflipTiebreaker(rng),
        ]

    def resolve(
        self,
        tied_teams: list[TeamStanding],
        all_standings: Standings,
    ) -> TiebreakerResult:
        """Apply tiebreakers until resolved."""
        if len(tied_teams) <= 1:
            return TiebreakerResult(True, None, tied_teams, "No tie")

        current_teams = tied_teams

        for rule in self.rules:
            result = rule.resolve(current_teams, all_standings)
            if result.resolved:
                return result
            current_teams = result.ordered_teams

        # Should never reach here if coinflip is last
        return TiebreakerResult(True, TiebreakerMethod.COINFLIP, current_teams)

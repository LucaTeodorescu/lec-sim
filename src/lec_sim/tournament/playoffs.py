"""Double-elimination playoff bracket logic."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from lec_sim.models.team import Team
from lec_sim.models.match import Match, MatchFormat, MatchResult


class BracketPosition(Enum):
    """Positions in double-elimination bracket for 8 teams."""

    # Upper Bracket Round 1 (Quarterfinals)
    UPPER_QF_1 = auto()  # Seed 1 vs Seed 8
    UPPER_QF_2 = auto()  # Seed 4 vs Seed 5
    UPPER_QF_3 = auto()  # Seed 2 vs Seed 7
    UPPER_QF_4 = auto()  # Seed 3 vs Seed 6

    # Upper Bracket Round 2 (Semifinals)
    UPPER_SF_1 = auto()  # Winner QF1 vs Winner QF2
    UPPER_SF_2 = auto()  # Winner QF3 vs Winner QF4

    # Upper Bracket Final
    UPPER_FINAL = auto()

    # Lower Bracket Round 1
    LOWER_R1_1 = auto()  # Loser QF1 vs Loser QF2
    LOWER_R1_2 = auto()  # Loser QF3 vs Loser QF4

    # Lower Bracket Round 2
    LOWER_R2_1 = auto()  # Winner LR1_1 vs Loser USF1
    LOWER_R2_2 = auto()  # Winner LR1_2 vs Loser USF2

    # Lower Bracket Semifinal
    LOWER_SF = auto()

    # Lower Bracket Final
    LOWER_FINAL = auto()

    # Grand Final
    GRAND_FINAL = auto()


@dataclass
class BracketSlot:
    """A slot in the bracket that holds a team."""

    position: BracketPosition
    team: Optional[Team] = None
    seed: Optional[int] = None


@dataclass
class PlayoffBracket:
    """Double-elimination playoff bracket for 8 teams."""

    teams: list[Team] = field(default_factory=list)  # Seeded 1-8
    matches: dict[BracketPosition, Match] = field(default_factory=dict)
    results: dict[BracketPosition, MatchResult] = field(default_factory=dict)

    # Track eliminated teams
    eliminated: set[Team] = field(default_factory=set)

    # Final placements
    champion: Optional[Team] = None
    runner_up: Optional[Team] = None
    third_place: Optional[Team] = None
    fourth_place: Optional[Team] = None

    def seed_teams(self, seeded_teams: list[Team]) -> None:
        """
        Seed 8 teams into the bracket.

        Standard seeding for upper bracket QFs:
        - 1 vs 8
        - 4 vs 5
        - 2 vs 7
        - 3 vs 6
        """
        if len(seeded_teams) != 8:
            raise ValueError("Exactly 8 teams required for playoffs")

        self.teams = seeded_teams

        # Create upper bracket quarterfinal matches
        self.matches[BracketPosition.UPPER_QF_1] = Match(
            team_a=seeded_teams[0],  # Seed 1
            team_b=seeded_teams[7],  # Seed 8
            format=MatchFormat.BO3,
            stage="upper_qf",
        )
        self.matches[BracketPosition.UPPER_QF_2] = Match(
            team_a=seeded_teams[3],  # Seed 4
            team_b=seeded_teams[4],  # Seed 5
            format=MatchFormat.BO3,
            stage="upper_qf",
        )
        self.matches[BracketPosition.UPPER_QF_3] = Match(
            team_a=seeded_teams[1],  # Seed 2
            team_b=seeded_teams[6],  # Seed 7
            format=MatchFormat.BO3,
            stage="upper_qf",
        )
        self.matches[BracketPosition.UPPER_QF_4] = Match(
            team_a=seeded_teams[2],  # Seed 3
            team_b=seeded_teams[5],  # Seed 6
            format=MatchFormat.BO3,
            stage="upper_qf",
        )

    def record_result(self, position: BracketPosition, result: MatchResult) -> None:
        """Record a match result and update bracket progression."""
        self.results[position] = result
        self._update_bracket_progression(position, result)

    def _update_bracket_progression(
        self, position: BracketPosition, result: MatchResult
    ) -> None:
        """Update bracket based on match result."""
        winner = result.winner
        loser = result.loser

        # Upper Bracket Quarterfinals -> Upper Semifinals + Lower R1
        if position == BracketPosition.UPPER_QF_1:
            self._set_or_create_match(BracketPosition.UPPER_SF_1, winner, is_team_a=True)
            self._set_or_create_match(BracketPosition.LOWER_R1_1, loser, is_team_a=True)
        elif position == BracketPosition.UPPER_QF_2:
            self._set_or_create_match(
                BracketPosition.UPPER_SF_1, winner, is_team_a=False
            )
            self._set_or_create_match(
                BracketPosition.LOWER_R1_1, loser, is_team_a=False
            )
        elif position == BracketPosition.UPPER_QF_3:
            self._set_or_create_match(BracketPosition.UPPER_SF_2, winner, is_team_a=True)
            self._set_or_create_match(BracketPosition.LOWER_R1_2, loser, is_team_a=True)
        elif position == BracketPosition.UPPER_QF_4:
            self._set_or_create_match(
                BracketPosition.UPPER_SF_2, winner, is_team_a=False
            )
            self._set_or_create_match(
                BracketPosition.LOWER_R1_2, loser, is_team_a=False
            )

        # Upper Semifinals -> Upper Final + Lower R2
        elif position == BracketPosition.UPPER_SF_1:
            self._set_or_create_match(
                BracketPosition.UPPER_FINAL, winner, is_team_a=True, fmt=MatchFormat.BO5
            )
            self._set_or_create_match(
                BracketPosition.LOWER_R2_1, loser, is_team_a=False
            )
        elif position == BracketPosition.UPPER_SF_2:
            self._set_or_create_match(
                BracketPosition.UPPER_FINAL, winner, is_team_a=False, fmt=MatchFormat.BO5
            )
            self._set_or_create_match(
                BracketPosition.LOWER_R2_2, loser, is_team_a=False
            )

        # Upper Final -> Grand Final (winner side)
        elif position == BracketPosition.UPPER_FINAL:
            self._set_or_create_match(
                BracketPosition.GRAND_FINAL, winner, is_team_a=True, fmt=MatchFormat.BO5
            )
            self._set_or_create_match(
                BracketPosition.LOWER_FINAL, loser, is_team_a=False, fmt=MatchFormat.BO5
            )

        # Lower R1 -> Lower R2
        elif position == BracketPosition.LOWER_R1_1:
            self._set_or_create_match(BracketPosition.LOWER_R2_1, winner, is_team_a=True)
            self.eliminated.add(loser)
        elif position == BracketPosition.LOWER_R1_2:
            self._set_or_create_match(BracketPosition.LOWER_R2_2, winner, is_team_a=True)
            self.eliminated.add(loser)

        # Lower R2 -> Lower SF
        elif position == BracketPosition.LOWER_R2_1:
            self._set_or_create_match(
                BracketPosition.LOWER_SF, winner, is_team_a=True, fmt=MatchFormat.BO5
            )
            self.eliminated.add(loser)
        elif position == BracketPosition.LOWER_R2_2:
            self._set_or_create_match(
                BracketPosition.LOWER_SF, winner, is_team_a=False, fmt=MatchFormat.BO5
            )
            self.eliminated.add(loser)

        # Lower SF -> Lower Final
        elif position == BracketPosition.LOWER_SF:
            self._set_or_create_match(
                BracketPosition.LOWER_FINAL, winner, is_team_a=True, fmt=MatchFormat.BO5
            )
            self.fourth_place = loser
            self.eliminated.add(loser)

        # Lower Final -> Grand Final (loser side)
        elif position == BracketPosition.LOWER_FINAL:
            self._set_or_create_match(
                BracketPosition.GRAND_FINAL, winner, is_team_a=False, fmt=MatchFormat.BO5
            )
            self.third_place = loser
            self.eliminated.add(loser)

        # Grand Final
        elif position == BracketPosition.GRAND_FINAL:
            self.champion = winner
            self.runner_up = loser
            self.eliminated.add(loser)

    def _set_or_create_match(
        self,
        position: BracketPosition,
        team: Team,
        is_team_a: bool,
        fmt: MatchFormat = MatchFormat.BO3,
    ) -> None:
        """Set a team in a match slot, creating the match if needed."""
        if position not in self.matches:
            if is_team_a:
                self.matches[position] = Match(
                    team_a=team,
                    team_b=team,  # Placeholder, will be replaced
                    format=fmt,
                    stage=position.name.lower(),
                )
            else:
                self.matches[position] = Match(
                    team_a=team,  # Placeholder
                    team_b=team,
                    format=fmt,
                    stage=position.name.lower(),
                )
        else:
            match = self.matches[position]
            if is_team_a:
                self.matches[position] = Match(
                    team_a=team,
                    team_b=match.team_b,
                    format=match.format,
                    stage=match.stage,
                    id=match.id,
                )
            else:
                self.matches[position] = Match(
                    team_a=match.team_a,
                    team_b=team,
                    format=match.format,
                    stage=match.stage,
                    id=match.id,
                )

    def get_next_matches(self) -> list[tuple[BracketPosition, Match]]:
        """Get all matches that are ready to be played (both teams set, not completed)."""
        ready = []
        for pos, match in self.matches.items():
            if pos not in self.results and match.team_a != match.team_b:
                ready.append((pos, match))
        return ready

    def is_complete(self) -> bool:
        """Check if the bracket is complete."""
        return self.champion is not None

    def get_placement(self, team: Team) -> Optional[int]:
        """Get final placement for a team (1-8)."""
        if team == self.champion:
            return 1
        elif team == self.runner_up:
            return 2
        elif team == self.third_place:
            return 3
        elif team == self.fourth_place:
            return 4
        elif team in self.eliminated:
            # 5th-8th based on when eliminated
            return 5  # Simplified; could track exact round
        return None

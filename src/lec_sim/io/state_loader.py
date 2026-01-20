"""Load tournament state from JSON files."""

import json
from pathlib import Path
from typing import Optional
from uuid import UUID

from lec_sim.models.team import Team
from lec_sim.models.match import Match, MatchFormat, MatchResult
from lec_sim.models.standing import Standings
from lec_sim.tournament.tournament import Tournament
from lec_sim.tournament.round_robin import generate_round_robin_schedule


# Default LEC 2026 Versus teams
DEFAULT_TEAMS = [
    Team(name="Fnatic", short_name="FNC"),
    Team(name="G2 Esports", short_name="G2"),
    Team(name="GIANTX", short_name="GX"),
    Team(name="Karmine Corp", short_name="KC"),
    Team(name="Shifters", short_name="SHFT"),
    Team(name="Team Vitality", short_name="VIT"),
    Team(name="Team Heretics", short_name="TH"),
    Team(name="Movistar KOI", short_name="MKOI"),
    Team(name="SK Gaming", short_name="SK"),
    Team(name="Natus Vincere", short_name="NAVI"),
    Team(name="Los Ratones", short_name="LR", is_erl=True),
    Team(name="Karmine Corp Blue", short_name="KCB", is_erl=True),
]


def get_default_teams() -> list[Team]:
    """Get the default LEC 2026 Versus teams."""
    return DEFAULT_TEAMS.copy()


def create_team_lookup(teams: list[Team]) -> dict[str, Team]:
    """Create a lookup dict from short_name to Team."""
    return {t.short_name: t for t in teams}


class StateLoader:
    """Load tournament state from JSON."""

    def __init__(self, teams: Optional[list[Team]] = None):
        """
        Initialize the state loader.

        Args:
            teams: List of teams. If None, uses default LEC 2026 teams.
        """
        self.teams = teams or get_default_teams()
        self._team_lookup = create_team_lookup(self.teams)

    def load_from_file(self, path: Path) -> Tournament:
        """Load tournament state from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        return self.load_from_dict(data)

    def load_from_dict(self, data: dict) -> Tournament:
        """Load tournament state from a dictionary."""
        # Create tournament with all possible matches
        tournament = Tournament.create_new(self.teams)

        # Process completed matches from data
        completed_matches = data.get("completed_matches", [])

        # Build a lookup for matches by teams
        match_lookup: dict[tuple[UUID, UUID], Match] = {}
        for match in tournament.round_robin_matches:
            key = tuple(sorted([match.team_a.id, match.team_b.id]))
            match_lookup[key] = match

        # Record completed match results
        for match_data in completed_matches:
            team_a_name = match_data.get("team_a")
            team_b_name = match_data.get("team_b")
            winner_name = match_data.get("winner")

            team_a = self._team_lookup.get(team_a_name)
            team_b = self._team_lookup.get(team_b_name)
            winner = self._team_lookup.get(winner_name)

            if not team_a or not team_b or not winner:
                continue  # Skip invalid entries

            loser = team_b if winner == team_a else team_a
            score = match_data.get("score", [1, 0])

            # Find the match in our schedule
            key = tuple(sorted([team_a.id, team_b.id]))
            match = match_lookup.get(key)

            if match:
                result = MatchResult(
                    winner=winner,
                    loser=loser,
                    winner_score=score[0],
                    loser_score=score[1],
                )
                tournament.record_round_robin_result(match, result)

        return tournament

    def get_team(self, short_name: str) -> Optional[Team]:
        """Get a team by short name."""
        return self._team_lookup.get(short_name)


def load_tournament_from_json(path: Path) -> Tournament:
    """Convenience function to load tournament from JSON file."""
    loader = StateLoader()
    return loader.load_from_file(path)


def create_empty_tournament() -> Tournament:
    """Create a new tournament with no completed matches."""
    return Tournament.create_new(get_default_teams())

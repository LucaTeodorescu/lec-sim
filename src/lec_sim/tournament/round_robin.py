"""Round-robin tournament stage logic."""

from itertools import combinations
from typing import Iterator

from lec_sim.models.team import Team
from lec_sim.models.match import Match, MatchFormat


def generate_round_robin_schedule(
    teams: list[Team],
    format: MatchFormat = MatchFormat.BO1,
) -> list[Match]:
    """
    Generate all matches for a single round-robin tournament.

    Each team plays every other team once.

    Args:
        teams: List of teams in the tournament
        format: Match format (default Bo1)

    Returns:
        List of Match objects (unplayed)
    """
    matches = []
    for team_a, team_b in combinations(teams, 2):
        match = Match(
            team_a=team_a,
            team_b=team_b,
            format=format,
            stage="round_robin",
        )
        matches.append(match)
    return matches


def get_remaining_matches(matches: list[Match]) -> list[Match]:
    """Get all matches that haven't been played yet."""
    return [m for m in matches if not m.is_completed]


def get_completed_matches(matches: list[Match]) -> list[Match]:
    """Get all matches that have been played."""
    return [m for m in matches if m.is_completed]


def get_matches_for_team(matches: list[Match], team: Team) -> list[Match]:
    """Get all matches involving a specific team."""
    return [m for m in matches if m.team_a == team or m.team_b == team]


def iter_matchups(teams: list[Team]) -> Iterator[tuple[Team, Team]]:
    """Iterate over all possible matchups."""
    yield from combinations(teams, 2)

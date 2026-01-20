"""Monte Carlo simulation engine."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
import random

from lec_sim.models.team import Team
from lec_sim.models.match import Match, MatchFormat, MatchResult
from lec_sim.models.standing import TeamStanding
from lec_sim.simulation.win_rates import WinRateMatrix
from lec_sim.tournament.tournament import Tournament
from lec_sim.tournament.playoffs import PlayoffBracket, BracketPosition


@dataclass
class SimulationConfig:
    """Configuration for Monte Carlo simulation."""

    num_simulations: int = 10000
    seed: Optional[int] = None


@dataclass
class SimulationOutcome:
    """Outcome of a single tournament simulation."""

    # Regular season final standings (team -> rank 1-12)
    regular_season_rank: dict[str, int] = field(default_factory=dict)

    # Did team make playoffs? (top 8)
    made_playoffs: set[str] = field(default_factory=set)

    # Playoff seeding (1-8)
    playoff_seed: dict[str, int] = field(default_factory=dict)

    # Final placement after playoffs
    final_placement: dict[str, int] = field(default_factory=dict)

    # Champion
    champion: Optional[str] = None


@dataclass
class SimulationResults:
    """Aggregated results from all simulations."""

    num_simulations: int

    # team_name -> probability of making playoffs
    playoff_probability: dict[str, float] = field(default_factory=dict)

    # team_name -> probability of winning championship
    championship_probability: dict[str, float] = field(default_factory=dict)

    # team_name -> {rank: probability}
    regular_season_distribution: dict[str, dict[int, float]] = field(
        default_factory=dict
    )

    # team_name -> {seed: probability} (for playoff seeds 1-8)
    seeding_distribution: dict[str, dict[int, float]] = field(default_factory=dict)

    # team_name -> {placement: probability} (final placement 1-8 in playoffs)
    playoff_placement_distribution: dict[str, dict[int, float]] = field(
        default_factory=dict
    )

    def print_summary(self) -> None:
        """Print a formatted summary of results."""
        print("\n" + "=" * 60)
        print("SIMULATION RESULTS")
        print("=" * 60)
        print(f"Simulations run: {self.num_simulations:,}")

        # Playoff Qualification
        print("\n" + "-" * 60)
        print("PLAYOFF QUALIFICATION PROBABILITY")
        print("-" * 60)
        print(f"{'Rank':<6} {'Team':<25} {'Prob':<10}")
        sorted_teams = sorted(
            self.playoff_probability.items(), key=lambda x: -x[1]
        )
        for i, (team, prob) in enumerate(sorted_teams, 1):
            marker = "---" if i == 8 else "   "
            print(f"{i:<6} {team:<25} {prob*100:>6.1f}%")
            if i == 8:
                print("       " + "-" * 40 + " (Playoff cutoff)")

        # Championship
        print("\n" + "-" * 60)
        print("CHAMPIONSHIP PROBABILITY")
        print("-" * 60)
        print(f"{'Rank':<6} {'Team':<25} {'Prob':<10}")
        sorted_champs = sorted(
            self.championship_probability.items(), key=lambda x: -x[1]
        )
        for i, (team, prob) in enumerate(sorted_champs[:8], 1):
            print(f"{i:<6} {team:<25} {prob*100:>6.1f}%")

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON export."""
        return {
            "num_simulations": self.num_simulations,
            "playoff_probability": self.playoff_probability,
            "championship_probability": self.championship_probability,
            "regular_season_distribution": self.regular_season_distribution,
            "seeding_distribution": self.seeding_distribution,
            "playoff_placement_distribution": self.playoff_placement_distribution,
        }


class SimulationEngine:
    """Monte Carlo simulation engine for tournament outcomes."""

    def __init__(
        self,
        tournament: Tournament,
        win_rates: WinRateMatrix,
        config: Optional[SimulationConfig] = None,
    ):
        self.tournament = tournament
        self.win_rates = win_rates
        self.config = config or SimulationConfig()
        self._rng = random.Random(self.config.seed)

    def simulate_match(self, match: Match, rng: random.Random) -> MatchResult:
        """Simulate a single match outcome."""
        prob_a_wins = self.win_rates.get_win_probability(
            match.team_a.id, match.team_b.id
        )

        if match.format == MatchFormat.BO1:
            a_wins = rng.random() < prob_a_wins
            winner = match.team_a if a_wins else match.team_b
            loser = match.team_b if a_wins else match.team_a
            return MatchResult(winner=winner, loser=loser, winner_score=1, loser_score=0)

        # Bo3/Bo5: simulate individual games
        games_to_win = match.format.games_to_win
        a_score, b_score = 0, 0

        while a_score < games_to_win and b_score < games_to_win:
            if rng.random() < prob_a_wins:
                a_score += 1
            else:
                b_score += 1

        if a_score > b_score:
            return MatchResult(
                winner=match.team_a,
                loser=match.team_b,
                winner_score=a_score,
                loser_score=b_score,
            )
        else:
            return MatchResult(
                winner=match.team_b,
                loser=match.team_a,
                winner_score=b_score,
                loser_score=a_score,
            )

    def simulate_playoffs(
        self, bracket: PlayoffBracket, rng: random.Random
    ) -> PlayoffBracket:
        """Simulate the entire playoff bracket."""
        # Process matches in order
        match_order = [
            # Upper QFs
            BracketPosition.UPPER_QF_1,
            BracketPosition.UPPER_QF_2,
            BracketPosition.UPPER_QF_3,
            BracketPosition.UPPER_QF_4,
            # Lower R1 (losers from QFs)
            BracketPosition.LOWER_R1_1,
            BracketPosition.LOWER_R1_2,
            # Upper SFs
            BracketPosition.UPPER_SF_1,
            BracketPosition.UPPER_SF_2,
            # Lower R2
            BracketPosition.LOWER_R2_1,
            BracketPosition.LOWER_R2_2,
            # Upper Final
            BracketPosition.UPPER_FINAL,
            # Lower SF
            BracketPosition.LOWER_SF,
            # Lower Final
            BracketPosition.LOWER_FINAL,
            # Grand Final
            BracketPosition.GRAND_FINAL,
        ]

        for position in match_order:
            if position in bracket.matches and position not in bracket.results:
                match = bracket.matches[position]
                # Make sure both teams are set (not placeholder)
                if match.team_a != match.team_b:
                    result = self.simulate_match(match, rng)
                    bracket.record_result(position, result)

        return bracket

    def run_single_simulation(self, seed: int) -> SimulationOutcome:
        """Run a single tournament simulation."""
        rng = random.Random(seed)
        tournament_copy = self.tournament.copy()

        # Simulate remaining round-robin matches
        for match in tournament_copy.get_remaining_round_robin_matches():
            result = self.simulate_match(match, rng)
            tournament_copy.record_round_robin_result(match, result)

        # Resolve tiebreakers and determine playoff seeding
        final_standings = tournament_copy.resolve_standings(rng)

        outcome = SimulationOutcome()

        # Record regular season ranks
        for rank, standing in enumerate(final_standings, 1):
            outcome.regular_season_rank[standing.team.name] = rank

        # Top 8 make playoffs
        playoff_teams = final_standings[:8]
        for seed, standing in enumerate(playoff_teams, 1):
            outcome.made_playoffs.add(standing.team.name)
            outcome.playoff_seed[standing.team.name] = seed

        # Simulate playoffs
        bracket = tournament_copy.create_playoff_bracket(playoff_teams)
        bracket = self.simulate_playoffs(bracket, rng)

        # Record final placements
        if bracket.champion:
            outcome.champion = bracket.champion.name
            outcome.final_placement[bracket.champion.name] = 1
        if bracket.runner_up:
            outcome.final_placement[bracket.runner_up.name] = 2
        if bracket.third_place:
            outcome.final_placement[bracket.third_place.name] = 3
        if bracket.fourth_place:
            outcome.final_placement[bracket.fourth_place.name] = 4

        # 5th-8th for teams eliminated in lower R2
        placement = 5
        for team in bracket.eliminated:
            if team.name not in outcome.final_placement:
                outcome.final_placement[team.name] = placement
                placement += 1

        return outcome

    def run(self) -> SimulationResults:
        """Run all Monte Carlo simulations."""
        # Generate seeds for reproducibility
        seeds = [self._rng.randint(0, 2**31) for _ in range(self.config.num_simulations)]

        outcomes = [self.run_single_simulation(s) for s in seeds]

        return self._aggregate_results(outcomes)

    def _aggregate_results(self, outcomes: list[SimulationOutcome]) -> SimulationResults:
        """Aggregate individual simulation outcomes into summary statistics."""
        n = len(outcomes)

        # Count occurrences
        playoff_counts: dict[str, int] = defaultdict(int)
        championship_counts: dict[str, int] = defaultdict(int)
        regular_season_counts: dict[str, dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        seeding_counts: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
        playoff_placement_counts: dict[str, dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for outcome in outcomes:
            # Playoff qualification
            for team_name in outcome.made_playoffs:
                playoff_counts[team_name] += 1

            # Championship
            if outcome.champion:
                championship_counts[outcome.champion] += 1

            # Regular season distribution
            for team_name, rank in outcome.regular_season_rank.items():
                regular_season_counts[team_name][rank] += 1

            # Seeding distribution
            for team_name, seed in outcome.playoff_seed.items():
                seeding_counts[team_name][seed] += 1

            # Playoff placement distribution
            for team_name, placement in outcome.final_placement.items():
                playoff_placement_counts[team_name][placement] += 1

        # Convert to probabilities
        return SimulationResults(
            num_simulations=n,
            playoff_probability={k: v / n for k, v in playoff_counts.items()},
            championship_probability={k: v / n for k, v in championship_counts.items()},
            regular_season_distribution={
                team: {rank: count / n for rank, count in ranks.items()}
                for team, ranks in regular_season_counts.items()
            },
            seeding_distribution={
                team: {seed: count / n for seed, count in seeds.items()}
                for team, seeds in seeding_counts.items()
            },
            playoff_placement_distribution={
                team: {place: count / n for place, count in places.items()}
                for team, places in playoff_placement_counts.items()
            },
        )

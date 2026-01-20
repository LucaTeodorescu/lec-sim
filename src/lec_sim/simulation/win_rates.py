"""Win rate matrix for calculating match probabilities."""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class WinRateMatrix:
    """
    Stores win probabilities between teams.

    matrix[team_a_id][team_b_id] = P(team_a beats team_b)
    """

    matrix: dict[UUID, dict[UUID, float]] = field(default_factory=dict)
    default_rate: float = 0.5

    def get_win_probability(self, team_a_id: UUID, team_b_id: UUID) -> float:
        """Get probability of team_a beating team_b."""
        if team_a_id in self.matrix and team_b_id in self.matrix[team_a_id]:
            return self.matrix[team_a_id][team_b_id]
        return self.default_rate

    def set_win_probability(
        self, team_a_id: UUID, team_b_id: UUID, prob: float
    ) -> None:
        """
        Set probability of team_a beating team_b.

        Automatically sets inverse for team_b vs team_a.
        """
        if not 0.0 <= prob <= 1.0:
            raise ValueError("Probability must be between 0 and 1")

        if team_a_id not in self.matrix:
            self.matrix[team_a_id] = {}
        if team_b_id not in self.matrix:
            self.matrix[team_b_id] = {}

        self.matrix[team_a_id][team_b_id] = prob
        self.matrix[team_b_id][team_a_id] = 1.0 - prob

    @classmethod
    def uniform(cls, rate: float = 0.5) -> "WinRateMatrix":
        """Create a matrix with uniform win rates."""
        return cls(default_rate=rate)

    @classmethod
    def from_elo_ratings(
        cls, elo_ratings: dict[UUID, float], k: float = 400
    ) -> "WinRateMatrix":
        """
        Generate win rate matrix from Elo ratings.

        P(A beats B) = 1 / (1 + 10^((Elo_B - Elo_A) / k))

        Args:
            elo_ratings: Mapping of team_id to Elo rating
            k: Elo scale factor (default 400)
        """
        matrix = cls()
        team_ids = list(elo_ratings.keys())

        for i, team_a in enumerate(team_ids):
            for team_b in team_ids[i + 1 :]:
                elo_a = elo_ratings[team_a]
                elo_b = elo_ratings[team_b]
                prob_a = 1 / (1 + 10 ** ((elo_b - elo_a) / k))
                matrix.set_win_probability(team_a, team_b, prob_a)

        return matrix

"""Results output and formatting."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from lec_sim.simulation.engine import SimulationResults


def save_results_to_json(
    results: SimulationResults,
    path: Optional[Path] = None,
    results_dir: Path = Path("data/results"),
) -> Path:
    """
    Save simulation results to a JSON file.

    Args:
        results: The simulation results to save
        path: Specific file path. If None, generates timestamped filename.
        results_dir: Directory for results (used if path is None)

    Returns:
        Path to the saved file
    """
    if path is None:
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = results_dir / f"sim_{timestamp}.json"

    data = {
        "timestamp": datetime.now().isoformat(),
        "results": results.to_dict(),
    }

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return path


def format_probability_table(
    probabilities: dict[str, float],
    title: str,
    show_cutoff_at: Optional[int] = None,
) -> str:
    """Format probabilities as a CLI table."""
    lines = []
    lines.append("")
    lines.append("-" * 50)
    lines.append(title)
    lines.append("-" * 50)
    lines.append(f"{'Rank':<6} {'Team':<25} {'Prob':<10}")

    sorted_items = sorted(probabilities.items(), key=lambda x: -x[1])

    for i, (team, prob) in enumerate(sorted_items, 1):
        lines.append(f"{i:<6} {team:<25} {prob*100:>6.1f}%")
        if show_cutoff_at and i == show_cutoff_at:
            lines.append("       " + "-" * 35 + " (cutoff)")

    return "\n".join(lines)


def format_distribution_table(
    distribution: dict[str, dict[int, float]],
    title: str,
    positions: list[int],
) -> str:
    """Format a distribution (ranks/seeds) as a table."""
    lines = []
    lines.append("")
    lines.append("-" * 70)
    lines.append(title)
    lines.append("-" * 70)

    # Header
    header = f"{'Team':<20}"
    for pos in positions:
        header += f"{pos:>6}"
    lines.append(header)

    # Sort teams by their probability at position 1
    sorted_teams = sorted(
        distribution.keys(),
        key=lambda t: distribution[t].get(1, 0),
        reverse=True,
    )

    for team in sorted_teams:
        row = f"{team:<20}"
        for pos in positions:
            prob = distribution[team].get(pos, 0)
            if prob > 0:
                row += f"{prob*100:>5.1f}%"
            else:
                row += f"{'--':>6}"
        lines.append(row)

    return "\n".join(lines)

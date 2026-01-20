"""Command-line interface for LEC simulation."""

import argparse
import sys
from pathlib import Path

from lec_sim.io.state_loader import StateLoader, create_empty_tournament
from lec_sim.io.results import save_results_to_json, format_probability_table
from lec_sim.simulation.engine import SimulationEngine, SimulationConfig
from lec_sim.simulation.win_rates import WinRateMatrix


def cmd_simulate(args: argparse.Namespace) -> int:
    """Run Monte Carlo simulation."""
    print("LEC 2026 Versus Monte Carlo Simulation")
    print("=" * 50)

    # Load tournament state
    if args.state:
        state_path = Path(args.state)
        if not state_path.exists():
            print(f"Error: State file not found: {state_path}")
            return 1

        print(f"Loading state from: {state_path}")
        loader = StateLoader()
        tournament = loader.load_from_file(state_path)

        completed = len(tournament.get_completed_round_robin_matches())
        remaining = len(tournament.get_remaining_round_robin_matches())
        print(f"Matches completed: {completed}")
        print(f"Matches remaining: {remaining}")
    else:
        print("Starting fresh tournament (no completed matches)")
        tournament = create_empty_tournament()

    # Create win rate matrix
    win_rates = WinRateMatrix.uniform(args.win_rate)

    # Configure simulation
    config = SimulationConfig(
        num_simulations=args.simulations,
        seed=args.seed,
    )

    print(f"\nRunning {config.num_simulations:,} simulations...")
    if args.seed:
        print(f"Random seed: {args.seed}")

    # Run simulation
    engine = SimulationEngine(tournament, win_rates, config)
    results = engine.run()

    # Print results
    results.print_summary()

    # Save results
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = None

    saved_path = save_results_to_json(results, output_path)
    print(f"\nResults saved to: {saved_path}")

    return 0


def cmd_standings(args: argparse.Namespace) -> int:
    """Show current standings."""
    if not args.state:
        print("Error: --state file required")
        return 1

    state_path = Path(args.state)
    if not state_path.exists():
        print(f"Error: State file not found: {state_path}")
        return 1

    loader = StateLoader()
    tournament = loader.load_from_file(state_path)

    print("\nCurrent Standings")
    print("=" * 40)
    print(f"{'Rank':<6} {'Team':<25} {'W-L':<10}")
    print("-" * 40)

    standings = tournament.standings.get_ordered()
    for i, standing in enumerate(standings, 1):
        record = f"{standing.wins}-{standing.losses}"
        print(f"{i:<6} {standing.team.name:<25} {record:<10}")

    completed = len(tournament.get_completed_round_robin_matches())
    total = len(tournament.round_robin_matches)
    print(f"\nMatches: {completed}/{total} completed")

    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    """Show remaining schedule."""
    if args.state:
        state_path = Path(args.state)
        if not state_path.exists():
            print(f"Error: State file not found: {state_path}")
            return 1

        loader = StateLoader()
        tournament = loader.load_from_file(state_path)
    else:
        tournament = create_empty_tournament()

    remaining = tournament.get_remaining_round_robin_matches()

    print("\nRemaining Matches")
    print("=" * 40)
    print(f"Total remaining: {len(remaining)}")
    print("-" * 40)

    for i, match in enumerate(remaining[:20], 1):  # Show first 20
        print(f"{i:>3}. {match.team_a.short_name} vs {match.team_b.short_name}")

    if len(remaining) > 20:
        print(f"... and {len(remaining) - 20} more matches")

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="LEC 2026 Versus Monte Carlo Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # simulate command
    sim_parser = subparsers.add_parser("simulate", help="Run Monte Carlo simulation")
    sim_parser.add_argument(
        "--state", "-s",
        help="Path to current state JSON file",
    )
    sim_parser.add_argument(
        "--simulations", "-n",
        type=int,
        default=10000,
        help="Number of simulations to run (default: 10000)",
    )
    sim_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility",
    )
    sim_parser.add_argument(
        "--win-rate", "-w",
        type=float,
        default=0.5,
        help="Default win rate for all matchups (default: 0.5)",
    )
    sim_parser.add_argument(
        "--output", "-o",
        help="Output file path for results JSON",
    )

    # standings command
    standings_parser = subparsers.add_parser("standings", help="Show current standings")
    standings_parser.add_argument(
        "--state", "-s",
        required=True,
        help="Path to current state JSON file",
    )

    # schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Show remaining schedule")
    schedule_parser.add_argument(
        "--state", "-s",
        help="Path to current state JSON file (optional)",
    )

    args = parser.parse_args()

    if args.command == "simulate":
        return cmd_simulate(args)
    elif args.command == "standings":
        return cmd_standings(args)
    elif args.command == "schedule":
        return cmd_schedule(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

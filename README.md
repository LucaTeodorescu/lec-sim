# LEC Simulation

Monte Carlo simulation for LEC 2026 Versus tournament outcomes. Simulate playoff qualification probabilities, championship odds, and seeding distributions from any point in the season.

## Features

- Monte Carlo simulation with configurable number of iterations
- Start from current tournament state (e.g., after Week 1)
- 50% default win rate or custom rates per matchup
- LEC-accurate tiebreaker resolution (Head-to-Head → Strength of Victory)
- Double-elimination playoff bracket simulation
- JSON export of results

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Clone and enter the project
cd lec-sim

# Install dependencies
uv sync
```

## Quick Start

```bash
# Run simulation from current Week 1 state
uv run lec-sim simulate --state data/current_state.json

# With more simulations and a fixed seed for reproducibility
uv run lec-sim simulate --state data/current_state.json -n 50000 --seed 42

# Show current standings
uv run lec-sim standings --state data/current_state.json

# Show remaining schedule
uv run lec-sim schedule --state data/current_state.json
```

## Commands

### `simulate`

Run Monte Carlo simulation.

```bash
uv run lec-sim simulate [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--state`, `-s` | Path to current state JSON file |
| `--simulations`, `-n` | Number of simulations (default: 10000) |
| `--seed` | Random seed for reproducibility |
| `--win-rate`, `-w` | Default win rate for all matchups (default: 0.5) |
| `--output`, `-o` | Output file path for results JSON |

### `standings`

Show current standings from a state file.

```bash
uv run lec-sim standings --state data/current_state.json
```

### `schedule`

Show remaining matches.

```bash
uv run lec-sim schedule --state data/current_state.json
```

## Project Structure

```
standings/
├── pyproject.toml              # Package config (uv/hatch)
├── config/
│   ├── tournament.yaml         # Tournament format rules
│   └── teams.yaml              # Team definitions
├── data/
│   ├── current_state.json      # Current match results (input)
│   └── results/                # Simulation output files
└── src/lec_sim/
    ├── models/
    │   ├── team.py             # Team dataclass
    │   ├── match.py            # Match, MatchResult, MatchFormat
    │   └── standing.py         # TeamStanding, Standings
    ├── tournament/
    │   ├── round_robin.py      # Round-robin schedule generation
    │   ├── playoffs.py         # Double-elimination bracket
    │   └── tournament.py       # Main tournament orchestration
    ├── simulation/
    │   ├── engine.py           # Monte Carlo simulation engine
    │   └── win_rates.py        # Win probability matrix
    ├── tiebreaker/
    │   └── resolver.py         # H2H, SoV, coinflip chain
    ├── io/
    │   ├── state_loader.py     # Load state from JSON
    │   └── results.py          # Output formatting
    └── cli.py                  # Command-line interface
```

## State File Format

The `current_state.json` file tracks completed matches:

```json
{
  "tournament": "LEC 2026 Versus",
  "snapshot_date": "2026-01-20",
  "week": 1,
  "completed_matches": [
    {
      "team_a": "FNC",
      "team_b": "G2",
      "winner": "FNC",
      "score": [1, 0],
      "week": 1,
      "day": 1
    }
  ]
}
```

### Team Short Names

| Team | Short Name |
|------|------------|
| Fnatic | `FNC` |
| G2 Esports | `G2` |
| GIANTX | `GX` |
| Karmine Corp | `KC` |
| Shifters | `SHFT` |
| Team Vitality | `VIT` |
| Team Heretics | `TH` |
| Movistar KOI | `MKOI` |
| SK Gaming | `SK` |
| Natus Vincere | `NAVI` |
| Los Ratones | `LR` |
| Karmine Corp Blue | `KCB` |

## Updating Results

To add new match results, edit `data/current_state.json`:

```json
{
  "completed_matches": [
    // ... existing matches ...
    {"team_a": "FNC", "team_b": "KC", "winner": "KC", "score": [1, 0], "week": 2, "day": 1}
  ]
}
```

Then re-run the simulation to see updated probabilities.

## Tournament Format

**LEC 2026 Versus** (formerly Winter Split):
- **Regular Season**: 12 teams, single round-robin (11 Bo1 matches per team)
- **Playoffs**: Top 8 teams, double elimination
  - Upper/Lower QF & R1-R2: Best-of-3
  - Semifinals, Finals, Grand Final: Best-of-5

**Tiebreakers** (in order):
1. Head-to-Head record
2. Strength of Victory (sum of beaten opponents' wins)
3. Coinflip (random)

## Output

Results are saved to `data/results/sim_YYYYMMDD_HHMMSS.json`:

```json
{
  "timestamp": "2026-01-20T12:00:00",
  "results": {
    "num_simulations": 10000,
    "playoff_probability": {"Fnatic": 0.85, ...},
    "championship_probability": {"Fnatic": 0.12, ...},
    "regular_season_distribution": {...},
    "seeding_distribution": {...}
  }
}
```

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

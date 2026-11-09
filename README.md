# Cessna 172 Glide & Stall Simulator

A 2D side-view engineering test of a Cessna 172 that loses its engine and glides. The only control is angle of attack. This is not a game.

**Status:** milestone M1, project skeleton. Aerodynamics, time integration, homework plots, and the interactive view are added in later milestones.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Run

```bash
python -m cessna_sim
```

This prints the mass, wing area, gravity, density model, and stall angle in use. The glide view and `python -m cessna_sim --hw` plots are not part of this milestone.

## Test

```bash
pytest
```

## Author

Sahand — MSc Aerospace Engineering (Flight Dynamics & Control), University of Tehran.

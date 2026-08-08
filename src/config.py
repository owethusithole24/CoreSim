"""Config: the single object that holds every tunable parameter for one run.

architecture_design.md Section 9 groups parameters into five families —
demand, network geometry, vehicle/IDM, control, output/run. We add fields to
a family only once a component that actually reads them exists (principle 4,
"configuration over code" — but there's no point configuring something
nothing uses yet). Right now only the engine exists, so Config only carries
the output/run timing fields and the RNG seed. Network, vehicle, control and
demand fields join this class in later steps.
"""

from dataclasses import dataclass


@dataclass
class Config:
    # --- output/run family (architecture_design.md §9) ---
    dt: float = 0.1          # simulation time step, seconds
    warmup_s: float = 0.0    # discarded lead-in before metrics count, seconds (§8.3)
    duration_s: float = 60.0 # simulated seconds to run *after* warm-up

    # --- shared across all families: the one seed everything derives from (§8.1) ---
    seed: int = 42

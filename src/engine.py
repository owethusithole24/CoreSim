"""Engine: the fixed-step clock and loop (architecture_design.md §2, §8).

This is step 1 of the build roadmap (§13): clock, loop, seeded RNG — and
nothing else yet. There is no network, no vehicles, no control, no output.
Each later step adds one more stage to step(), in the exact order §2 fixes:
control -> vehicles -> network -> output -> viz. Keeping that order out of
the gate (even though most stages are still empty) is what stops a vehicle
from ever reacting to a signal that hasn't updated yet once those stages
exist.
"""

import random

from src.config import Config


class Engine:
    def __init__(self, config: Config):
        self.config = config
        self.rng = random.Random(config.seed)  # the one RNG everything else must use (§8.1)
        self.tick = 0   # number of step() calls so far — the ground truth for time

    @property
    def t(self) -> float:
        """Simulated seconds elapsed, derived from tick * dt (not accumulated).

        Repeatedly doing `t += dt` drifts: 0.1 added to itself ten times is
        0.9999999999999999, not 1.0, because 0.1 has no exact binary
        representation. Over thousands of ticks that drift compounds and can
        flip a `t < total` comparison the wrong way (it did, in an early
        version of this file — see the test that caught it). Deriving t from
        an integer tick count sidesteps the whole problem: multiplication
        error doesn't accumulate the way repeated addition does.
        """
        return self.tick * self.config.dt

    @property
    def is_warmed_up(self) -> bool:
        """True once the warm-up lead-in (§8.3) has elapsed and metrics should count."""
        return self.t >= self.config.warmup_s

    def step(self):
        """Advance the simulation by exactly one dt."""
        self.tick += 1

    def run(self):
        """Step until warmup_s + duration_s of simulated time has elapsed."""
        total = self.config.warmup_s + self.config.duration_s
        while self.t < total:
            self.step()

"""The Intelligent Driver Model (architecture_design.md §6.2, Treiber & Kesting
2010). One equation answers "how hard should this vehicle accelerate or
brake", given its own speed, the gap to whatever's ahead of it (a leader
vehicle, or later a red light / stop line modelled as a stationary virtual
leader), and how fast that gap is closing. Free-flow, following, and
stopping all fall out of this one formula — no special cases.
"""

import math

from src.config import IDMConfig


def idm_acceleration(speed: float, gap: float | None, closing_speed: float, idm: IDMConfig) -> float:
    """
    speed: this vehicle's current speed, m/s.
    gap: bumper-to-bumper distance to whatever is ahead, m. None means the
         road ahead is clear (no leader) — only the free-road term applies.
    closing_speed: speed - leader_speed. How much faster this vehicle is
         going than whatever's ahead. Ignored when gap is None.
    """
    free_road_term = (speed / idm.v0) ** idm.delta

    if gap is None:
        interaction_term = 0.0
    else:
        safe_gap = max(gap, 1e-3)  # guard divide-by-zero if gap ever hits ~0
        desired_gap = idm.s0 + max(
            0.0,
            speed * idm.T + (speed * closing_speed) / (2 * math.sqrt(idm.a_max * idm.b)),
        )
        interaction_term = (desired_gap / safe_gap) ** 2

    return idm.a_max * (1 - free_road_term - interaction_term)

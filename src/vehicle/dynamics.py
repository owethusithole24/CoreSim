"""Stepping a group of vehicles that share one link (architecture_design.md
§2, §4.2): find each vehicle's leader, ask the IDM for an acceleration,
then move everyone.
"""

from src.config import IDMConfig
from src.vehicle.idm import idm_acceleration
from src.vehicle.vehicle import Vehicle


def step_vehicles_on_link(vehicles: list[Vehicle], dt: float, idm: IDMConfig) -> None:
    """Advance every vehicle on one link by one dt.

    Position increases in the direction of travel, so the vehicle with the
    largest position is furthest along the link — the front of the queue —
    and has no leader (yet: a red light / stop line will occupy that role
    once Control exists, step 5). Every other vehicle's leader is whichever
    vehicle is immediately ahead of it, i.e. the next-largest position.

    Every vehicle's acceleration is computed from the *current* positions
    and speeds before any vehicle moves — mirroring the engine's own
    control-then-decide-then-move discipline (§2) at vehicle scale. Moving
    vehicles one at a time as we go would let a follower react to a leader
    that has already moved this tick, which isn't what happens in reality
    inside a single instant.
    """
    ordered = sorted(vehicles, key=lambda v: v.position)

    accelerations = []
    for i, vehicle in enumerate(ordered):
        if i == len(ordered) - 1:
            gap = None
            closing_speed = 0.0
        else:
            leader = ordered[i + 1]
            gap = leader.position - leader.length - vehicle.position
            closing_speed = vehicle.speed - leader.speed
        accelerations.append(idm_acceleration(vehicle.speed, gap, closing_speed, idm))

    for vehicle, acceleration in zip(ordered, accelerations):
        vehicle.acceleration = acceleration
        vehicle.integrate(dt)

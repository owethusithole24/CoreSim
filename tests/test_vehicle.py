"""Tests for Vehicle.integrate() — the ballistic update (§4.3) — checked
against plain kinematics, independent of the IDM equation that produces
the acceleration it's given.
"""

from src.vehicle.vehicle import Vehicle


def test_integrate_matches_constant_acceleration_kinematics():
    v = Vehicle(id=1, position=0.0, speed=10.0, acceleration=2.0)
    v.integrate(dt=1.0)

    # x = x0 + v0*t + 0.5*a*t^2 ; v = v0 + a*t
    assert v.position == 10.0 + 0.5 * 2.0 * 1.0 ** 2
    assert v.speed == 12.0


def test_hard_braking_never_produces_negative_speed():
    v = Vehicle(id=1, position=0.0, speed=1.0, acceleration=-10.0)
    v.integrate(dt=1.0)
    assert v.speed == 0.0


def test_a_stationary_vehicle_with_zero_acceleration_does_not_move():
    v = Vehicle(id=1, position=5.0, speed=0.0, acceleration=0.0)
    v.integrate(dt=1.0)
    assert v.position == 5.0
    assert v.speed == 0.0

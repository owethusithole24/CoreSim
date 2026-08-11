"""Scenario-level tests for step_vehicles_on_link — the "first provable
physics" milestone from architecture_design.md §12: a lone car reaches its
desired speed, and a following car never collides with its leader.
"""

from src.config import IDMConfig
from src.vehicle.dynamics import step_vehicles_on_link
from src.vehicle.vehicle import Vehicle


def run_for(vehicles, seconds, dt, idm):
    ticks = int(seconds / dt)
    for _ in range(ticks):
        step_vehicles_on_link(vehicles, dt, idm)


def test_a_lone_vehicle_accelerates_to_and_holds_desired_speed():
    idm = IDMConfig()
    car = Vehicle(id=1, position=0.0, speed=0.0)

    run_for([car], seconds=60.0, dt=0.1, idm=idm)

    assert abs(car.speed - idm.v0) < 0.01
    assert car.acceleration == 0.0 or abs(car.acceleration) < 1e-3


def test_a_following_vehicle_never_collides_with_a_slower_leader():
    idm = IDMConfig()
    # leader starts far ahead, already at desired speed and staying there
    # (position reset each tick so it acts like a car cruising at v0)
    leader = Vehicle(id=1, position=100.0, speed=idm.v0)
    follower = Vehicle(id=2, position=0.0, speed=0.0)

    dt = 0.1
    for _ in range(int(300.0 / dt)):
        step_vehicles_on_link([leader, follower], dt, idm)
        gap = leader.position - leader.length - follower.position
        assert gap > 0, "follower collided with leader"

    # after enough time, follower should have settled into following the
    # leader's speed rather than still accelerating toward it
    assert abs(follower.speed - leader.speed) < 0.1


def test_step_vehicles_on_link_is_independent_of_input_list_order():
    idm = IDMConfig()
    a = Vehicle(id=1, position=0.0, speed=5.0)
    b = Vehicle(id=2, position=20.0, speed=5.0)

    a2 = Vehicle(id=1, position=0.0, speed=5.0)
    b2 = Vehicle(id=2, position=20.0, speed=5.0)

    step_vehicles_on_link([a, b], dt=0.1, idm=idm)
    step_vehicles_on_link([b2, a2], dt=0.1, idm=idm)

    assert a.position == a2.position
    assert b.position == b2.position

"""Entry point. Runs two small demos:

1. the bare engine clock + RNG (proves timing/seeding work end to end)
2. two vehicles on one link, printed once per simulated second (proves the
   physics: free-flow acceleration and car-following, no collision)

There's no network/control integration yet — vehicles aren't attached to a
real Link, and there's no red light/stop line for them to react to (that's
step 5). This is what "first provable physics" looks like on the terminal
before the Pygame viewer exists to show it visually instead.
"""

from src.config import Config
from src.engine import Engine
from src.vehicle.dynamics import step_vehicles_on_link
from src.vehicle.vehicle import Vehicle


def run_engine_demo(config: Config) -> None:
    engine = Engine(config)
    engine.run()

    print(f"Ran {engine.tick} ticks of dt={config.dt}s -> t={engine.t:.2f}s")
    print(f"First 3 RNG draws from seed={config.seed}: "
          f"{[round(engine.rng.random(), 4) for _ in range(3)]}")


def run_vehicle_demo(config: Config) -> None:
    idm = config.idm
    leader = Vehicle(id=1, position=100.0, speed=0.0)
    follower = Vehicle(id=2, position=0.0, speed=0.0)

    print(f"\nTwo vehicles, one link, dt={config.dt}s, v0={idm.v0:.1f} m/s")
    header = f"{'t (s)':>6} {'leader pos':>11} {'leader v':>9} {'follower pos':>13} {'follower v':>11} {'gap':>7}"
    print(header)

    ticks = int(config.duration_s / config.dt)
    print_every = int(1.0 / config.dt)  # once per simulated second

    for tick in range(1, ticks + 1):
        step_vehicles_on_link([leader, follower], config.dt, idm)
        if tick % print_every == 0:
            gap = leader.position - leader.length - follower.position
            t = tick * config.dt
            print(f"{t:6.1f} {leader.position:11.1f} {leader.speed:9.2f} "
                  f"{follower.position:13.1f} {follower.speed:11.2f} {gap:7.1f}")


if __name__ == "__main__":
    config = Config(dt=0.1, duration_s=30.0, seed=42)
    run_engine_demo(config)
    run_vehicle_demo(config)

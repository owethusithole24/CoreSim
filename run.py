"""Entry point. Right now: build a Config, run the bare engine, report the clock.

There's no traffic yet — this just proves the loop and seeding work end to
end before we build anything that depends on them (network, vehicles,
control). Later steps will add --scenario / --headless / --seed flags here.
"""

from src.config import Config
from src.engine import Engine

if __name__ == "__main__":
    config = Config(dt=0.1, duration_s=10.0, seed=42)
    engine = Engine(config)
    engine.run()

    print(f"Ran {engine.tick} ticks of dt={config.dt}s -> t={engine.t:.2f}s")
    print(f"First 3 RNG draws from seed={config.seed}: "
          f"{[round(engine.rng.random(), 4) for _ in range(3)]}")

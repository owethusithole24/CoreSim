"""Vehicle: one vehicle's state (architecture_design.md §4.1)."""

from dataclasses import dataclass


@dataclass
class Vehicle:
    id: int
    position: float           # metres from the start of its current link
    speed: float = 0.0        # m/s
    acceleration: float = 0.0 # m/s^2, last value computed by the car-following model
    length: float = 5.0       # m — so followers keep a real (bumper-to-bumper) gap

    def integrate(self, dt: float) -> None:
        """Ballistic update (§4.3): turn this tick's acceleration into a new
        speed and position.

        Position is updated using the speed *before* this tick's
        acceleration is applied, not after. That's what makes this exact
        for constant acceleration over the step (standard kinematics:
        x = x0 + v0*t + 0.5*a*t^2) — using the updated speed instead (naive
        Euler) would make a braking vehicle travel further than it actually
        would, which matters once vehicles are stopping at signals.
        """
        self.position += self.speed * dt + 0.5 * self.acceleration * dt ** 2
        self.speed = max(0.0, self.speed + self.acceleration * dt)

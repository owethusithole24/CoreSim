# Four-Way Stop Queuing Demo — run guide & presentation notes

A small Pygame program that shows a four-way stop **as a queuing system**. It's a
learning stepping-stone toward the full microsimulation, and a source of visuals
for your Thursday presentation on implementation steps.

---

## Running it

You need Python 3 and Pygame 2.

```bash
pip install pygame
python four_way_stop_queue_demo.py
```

A window opens: the intersection on the left, a live stats + theory panel on the right.

If `pip install pygame` complains, try `pip3` or `python -m pip install pygame`.

---

## Controls

| Key | Action |
|---|---|
| **UP / DOWN** | increase / decrease arrival rate λ (per approach) |
| **RIGHT / LEFT** | increase / decrease mean service time (RIGHT = slower server) |
| **SPACE** | pause / resume |
| **F** | fast-forward ×4 (fills queues quickly for a screenshot) |
| **R** | reset stats and re-seed (reproducible run) |
| **ESC / Q** | quit |

---

## What each number means

- **λ per approach / λ total** — arrival rate. Vehicles arrive as a Poisson process; λ total = 4 × λ per approach.
- **mean service time / μ** — how long the intersection is busy per vehicle, and its inverse, the service rate μ.
- **ρ = λ/μ** — *utilisation*. The single most important number. ρ < 1 means the server can keep up; ρ ≥ 1 means it can't and the queue grows without bound. Colour-coded green → amber → red.
- **total in queue / max queue** — vehicles currently and ever stopped and waiting.
- **avg wait at line** — mean seconds a vehicle sits at the stop line before it's served.
- **throughput** — vehicles served per minute (the intersection's realised capacity).
- **M/M/1 Lq vs observed avg queue** — the theoretical average queue length from queuing theory, next to what the simulation actually produced. When ρ ≥ 1 the theory says "unbounded", and you'll watch the sim agree.

Vehicle colours: **blue** = approaching, **orange** = stopped/queuing, **green** = currently being served (crossing).

---

## How this maps to queuing theory (your Chapter 2.3)

This is the sentence for your slides: *a four-way stop is four queues competing for one server.* The intersection can only let one vehicle through at a time (first-come-first-served priority rules), so it behaves exactly like the single-channel queue Garber & Hoel (2009) describe — arrivals (vehicles), a queue (the waiting line), and a service facility (the intersection). Because arrivals are Poisson and service times are exponential, the pooled system is an **M/M/1 queue**, so the classic result applies:

> As the ratio of arrival rate to service rate (ρ) approaches 1, the expected number of vehicles in the system tends toward infinity. — Garber & Hoel (2009)

The demo lets you *see* that result instead of just reading it.

---

## Suggested screenshots + talking points for Thursday

Run these three states (use **F** to fill queues fast, then screenshot):

1. **Stable (ρ ≈ 0.64).** Default settings. Short, steady queues; throughput keeps up with arrivals. Caption: *"Under-saturated: service rate exceeds arrival rate, queues stay bounded."*
2. **Near capacity (ρ ≈ 0.9).** Press **UP** a few times (λ ≈ 0.11). Queues get long and volatile; the queue chart swings. Caption: *"As ρ → 1, small changes in demand cause large swings in delay."*
3. **Over-saturated (ρ ≥ 1.0).** Press **UP** until ρ passes 1 (λ ≈ 0.13+). Queues grow off-screen and never recover; observed avg queue keeps climbing. Caption: *"Over-saturated: demand exceeds capacity, queue grows without bound — this is the congestion the study targets."*

The **queue-length-over-time chart** in the panel is the most presentation-friendly image — screenshot it in each of the three states to show the qualitative change.

### How to frame it as "the road ahead"

This demo deliberately shows the **queuing core in isolation** — a single shared server, no car-following physics, no signals. Your talking points for the implementation plan:

- *What this proves:* I can model arrivals, a queue, a server, and measure delay/throughput — the evaluation metrics from my proposal.
- *What the full artifact adds on top:* individual car-following behaviour (IDM), the real corridor geometry (spacing between intersections), and swappable **control** — replacing these fixed first-come-first-served stop rules with a fixed-time signal, then a coordinated signal network.
- *Why that matters:* this demo shows congestion *building* at a saturated stop; the full simulation will test whether signalisation and coordination move the ρ-vs-delay curve in the right direction.

---

## Honest limitations (good to state, shows rigor)

- It's **not** the final artifact — no car-following model, no vehicle acceleration profile, no real geometry. Vehicles move at constant speed and stop instantly. That's intentional: the point is the queuing behaviour, not realistic motion.
- The M/M/1 comparison is an **approximation** — real vehicles take time to travel from spawn to the stop line, which M/M/1 ignores, so observed and theoretical queues won't match exactly. The *trend* (blow-up near ρ = 1) is what's faithful.
- Single-lane approaches, no turning conflicts modelled beyond one-at-a-time service.

Stating these limitations is itself a good slide — it shows you know the difference between the stepping-stone and the real artifact.

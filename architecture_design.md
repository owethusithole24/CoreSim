# Architecture Design — Corridor Traffic Microsimulation

**Project:** Designing microsimulations for analysing traffic control alternatives on a small scale
**Author:** Owethu Jazmene Sithole (41380525) · Supervisor: Prof Susan Campher
**Document status:** Simulation Design phase — v1 (living document, will be refined during implementation)
**Purpose:** This is the architectural blueprint for the artifact. It defines *what* we build, *how* the parts fit together, and — importantly for your defence — *why* each decision was made and how it traces back to your proposal and literature review.

---

## How to read this document

Every major section ends with a short **"Why / defend it"** note. That note is the sentence you should be able to say out loud to an examiner. If you can explain the "why", you own the design. Read the document top to bottom once; you don't need to understand the code yet, only the shape of the system and the reasoning.

Nothing here is locked. This is the design we implement against, but Design Science Research is explicitly iterative (Hevner et al., 2004), so we expect to revise it as we build. "Open decisions" are collected at the end.

---

## 1. Design principles

These are the rules everything else obeys. They come straight from your proposal, so they are defensible by construction.

1. **Simplicity without simplism.** Model the minimum set of behaviours needed to compare control alternatives, and no more. This is your Chapter 2 conclusion and your DSR "design as a search process" guideline — deliberately represent only a subset of the relevant means, ends and laws to keep the solution space feasible.
2. **Separate the engine from the picture.** The simulation logic (physics, control, metrics) runs independently of the Pygame visuals. You can run it with the window open to *watch*, or headless (no window) to *measure*. This is the single most important structural decision and Section 8 explains why.
3. **Deterministic and reproducible.** Given the same configuration and the same random seed, the simulation produces byte-for-byte identical output every run. This is what makes your "reliability" evaluation criterion demonstrable rather than aspirational.
4. **Configuration over code.** Every parameter from your Chapter 2.5 list lives in one config object, not scattered through the code. Changing a scenario means changing config, not rewriting logic. This is what makes "configurability" real.
5. **Four components, clean seams.** Your methodology commits to network / vehicle / control / output. We honour that exactly, with narrow, well-defined interfaces between them so each can be understood, tested, and explained on its own.

**Why / defend it:** each principle is a direct instantiation of a claim you already made in the proposal. When asked "why is your architecture shaped this way?", the honest answer is "because my methodology and literature review demanded these five properties."

---

## 2. High-level architecture

The system is a **time-stepped (discrete-time) microscopic simulation**. Think of it as a film: we advance a small clock by a fixed step `dt` (e.g. 0.1 s), and on each tick every vehicle re-evaluates what to do and moves a little. Run thousands of ticks and you have minutes of simulated traffic.

```
                    ┌──────────────────────────┐
                    │      Configuration       │   one object holding every
                    │  (parameters + seed)     │   parameter + the RNG seed
                    └────────────┬─────────────┘
                                 │ builds
                                 ▼
   ┌───────────────────────────────────────────────────────────┐
   │                    SIMULATION ENGINE                       │
   │                  (the fixed-step loop)                     │
   │                                                            │
   │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐  │
   │   │ NETWORK  │   │ VEHICLE  │   │ CONTROL  │   │ OUTPUT │  │
   │   │  model   │◄─►│  model   │◄─►│  model   │──►│metrics │  │
   │   └──────────┘   └──────────┘   └──────────┘   └────────┘  │
   │     roads &        car-following   stop rules /   delay,   │
   │     lanes &        + movement      signals /      queues,  │
   │     spacing                        offsets        etc.     │
   └───────────────────────────┬───────────────────────────────┘
                               │ read-only state
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        ┌─────────────────┐         ┌─────────────────┐
        │  VISUALISATION  │         │   CSV / RESULTS  │
        │    (Pygame)     │         │     logging      │
        │   optional      │         │                  │
        └─────────────────┘         └─────────────────┘
```

The four components in the middle are your methodology's four components. The engine is the loop that drives them. The two boxes at the bottom are two different *consumers* of the same simulation state — one draws it, one records it — and crucially neither is allowed to change the simulation.

**Data-flow in one tick (this is the heartbeat of the whole artifact):**

1. **Control** updates first — each intersection advances its internal clock (a signal may switch green→amber, a stop decides whose turn it is).
2. **Vehicles** each compute an acceleration from the car-following model, looking at (a) their leader vehicle and (b) any "virtual obstacle" the control places in front of them (a red light or a stop line — see Section 5.4).
3. **Vehicles** integrate that acceleration into a new speed and position.
4. **Network** handles hand-offs — a vehicle reaching the end of a link moves onto the next link / through the intersection.
5. **Output** samples metrics (queue lengths every second, vehicles that just completed their trip, etc.).
6. **Visualisation** (if the window is open) draws the current state.
7. Clock advances by `dt`; repeat.

**Why / defend it:** microscopic modelling means each vehicle is updated individually every step (your Chapter 2.4 justification). A fixed time-step loop is the standard, simplest, and most explainable way to do this — it is exactly how both MovSim and the Gandhi reference simulation advance time. The strict ordering (control → decide → move → hand-off → measure) prevents subtle bugs like a car reacting to a light that hasn't updated yet.

---

## 3. Component 1 — Network model

**Responsibility:** represent the physical road layout — where the roads are, how long they are, how many lanes, and how the intersections connect them. It holds *geometry and topology*, nothing that moves.

### 3.1 The building blocks

- **`Node` (intersection):** a point where roads meet. Each node owns a *control* (Section 5). Your corridor has four nodes.
- **`Link` (road segment / approach):** a one-directional stretch of road connecting two nodes, with a length (metres) and a speed limit. A two-way road between two intersections is two links (one each way). Vehicles live "on" a link at some position measured in metres from its start.
- **`Lane`:** a link may have one or more lanes. For version 1 we model **one lane per link per direction** and treat turning as a routing choice rather than a physical lane change (see Open Decisions). This keeps us out of lane-changing logic (MOBIL), which your scope explicitly allows us to simplify.
- **`Corridor` / `Network`:** the container that holds all nodes and links and knows how they connect (the topology).

### 3.2 Mapping your actual corridor

From your Figure 2 and problem description, the corridor is a chain of four intersections. As I read it (please confirm in the Open Decisions):

```
   [Signal A] ──── [4-way stop] ──── [Signal B] ──── [MAIN GATE 4-way stop]
    upstream         upstream         upstream          (primary subject)
```

Every intersection is a `Node`; every road segment between them (and the entry/exit stubs at each end and each side street) is a `Link`. The **main gate stop** is the intersection whose control we swap across the three scenarios; the upstream signals are what make coordination meaningful.

This layout is *data*, not code. It lives in the config as a small description ("node here, link of length L there"), which means when your supervisor asks "what if the stop were 50 m further from Signal B?", you change one number.

**Why / defend it:** this node-link representation is the universal way road networks are modelled (it is the basis of the OpenDRIVE standard MovSim uses, just radically simplified). Representing intersection spacing explicitly as link length is essential because your literature (Chapter 2.5, network geometry parameters) identifies spacing as a first-class variable — short spacing between your signals is the whole reason coordination matters.

---

## 4. Component 2 — Vehicle model

**Responsibility:** represent each individual vehicle and decide how it moves each tick. This is the heart of a *microscopic* model.

### 4.1 Vehicle state

Each `Vehicle` carries:

| Field | Meaning | Why it's here |
|---|---|---|
| `position` | metres along its current link | where it is |
| `speed` | current speed (m/s) | how fast |
| `acceleration` | current accel (m/s²) | output of the car-following model each tick |
| `length` | vehicle length (m) | so followers keep a real gap; affects queue length |
| `route` | the sequence of links it will take (its turning plan) | encodes turning-movement decisions |
| `desired_speed` | the speed it *wants* (free-flow) | per-driver variation |
| entry time / metrics | when it entered, time spent stopped, etc. | feeds the Output component |

### 4.2 How a vehicle decides to move

Every tick, a vehicle asks one question: *"given the thing in front of me, how hard should I accelerate or brake?"* The "thing in front" is whichever is closer:

- the **leader** — the vehicle ahead on the same link, or
- a **virtual obstacle** — a red/amber signal or an unsignalised stop line, which the Control component represents as a stationary "phantom vehicle" at the stop position.

That single question is answered by the **car-following model**. Section 6 compares the two candidate models in full — this is the decision you asked me to lay out.

### 4.3 Integration (turning acceleration into motion)

Once we have an acceleration `a`, we update speed and position. We use **ballistic update** (a standard, stable choice):

```
new_speed    = max(0, speed + a * dt)
new_position = position + speed * dt + 0.5 * a * dt²
```

The `max(0, …)` stops a braking car from rolling backwards. We'll discuss why ballistic beats naive Euler when we implement it — it matters for clean stopping behaviour.

**Why / defend it:** modelling per-vehicle speed, position and the leader relationship *is* the definition of microscopic car-following (Ferrara et al., 2018; Kesting & Treiber, 2008), which your Chapter 2 selects as the appropriate model class. The virtual-obstacle trick (4.2) is the elegant part: it lets **one** movement model handle free driving, following, *and* stopping at controls, instead of three separate special cases — which is exactly the kind of simplification your DSR "search process" guideline calls for.

---

## 5. Component 3 — Control model

**Responsibility:** decide, at each intersection, who is allowed to proceed. This is where your three scenarios actually differ — and the design's key insight is that **the network and vehicles never change across scenarios; only the control does.**

### 5.1 A common interface

Every control type implements the same tiny contract:

```
class IntersectionControl:
    def update(self, dt): ...          # advance internal clocks
    def may_proceed(self, vehicle): -> bool   # can THIS vehicle enter the intersection now?
    def stop_line_obstacle(self, approach): -> obstacle or None   # phantom vehicle for red/stop
```

Because all three controls share this interface, the vehicle and network code calls them identically and never needs to know which one it's talking to. Swapping scenarios = swapping the object behind this interface. (This is the "strategy pattern" — worth naming in your write-up.)

### 5.2 Scenario 1 — `StopControl` (baseline four-way stop)

Models the current reality: first-come-first-served with gap acceptance.

- Each approaching vehicle must first **halt at the stop line** (the control gives it a stop-line obstacle until it has stopped).
- Vehicles are served in **arrival order** (a queue of "who stopped first").
- A vehicle at the front may proceed only when the **conflict zone is clear** — i.e. no other vehicle is currently crossing (a simple reservation/occupancy flag on the node), which is a minimal **gap-acceptance / critical-gap** rule.

### 5.3 Scenario 2 — `FixedTimeSignal` (isolated traffic light)

Models a single signalised intersection.

- A **cycle** of fixed length made of **phases** (e.g. N-S green, then amber, then E-W green, then amber), each with a fixed duration: green / amber / red per approach.
- The control simply advances a clock through the cycle. An approach that isn't green gets a stop-line obstacle.
- Parameters: `cycle_length`, per-phase `green/amber/red` durations, `phase_sequence`, `lost_time`.

You chose fixed-time over actuated deliberately (Chapter 2.2) — it's parameterisable, cheap, and comparable. We honour that.

### 5.4 Scenario 3 — `CoordinatedNetwork` (green wave)

Models multiple `FixedTimeSignal`s that share timing so a platoon released by the upstream signal arrives at the next on green.

- The mechanism is a single extra parameter per signal: the **offset** — how many seconds this signal's cycle is shifted relative to a reference signal.
- Everything else is just two or more `FixedTimeSignal` objects. Coordination is *emergent* from well-chosen offsets, not new machinery.

### 5.5 The stop-line-as-obstacle bridge

Note how 5.2–5.4 all ultimately produce the same thing: a **stop-line obstacle** when a vehicle may not proceed, and nothing when it may. That's the only channel through which control talks to vehicles. So the vehicle model stays blissfully unaware of *why* it's stopping — red light or four-way stop, it's the same phantom obstacle feeding the same car-following equation.

**Why / defend it:** this is the architectural payoff. Your research question is a *comparison* of control alternatives on the *same* corridor and demand. By isolating everything that differs into one swappable component behind one interface, you guarantee a fair comparison (identical roads, identical vehicles, identical demand — only the control changes) and you make the code for each scenario small enough to fully explain. Fixed-time and offset-based coordination are exactly the two mechanisms your Chapter 2 concludes are most relevant.

---

## 6. The car-following decision — IDM vs simplified

You asked me to compare rather than pick for you. Here is the full comparison, then my recommendation.

Both models answer the same question — *"what acceleration should this vehicle use, given its speed, its leader's speed, and the gap to the leader?"* — but with different fidelity.

### 6.1 Option A — Simplified kinematic (follow-the-leader)

A minimal rule. One common form: each tick, the vehicle targets the **smaller** of (a) its desired speed and (b) a "safe speed" that wouldn't cause a collision given the current gap, then accelerates/brakes toward that target at fixed rates.

```
target_speed = min(desired_speed, safe_speed(gap, leader_speed))
if speed < target_speed:  accelerate at +a_max
else:                     brake at -b
```

- **Parameters (≈3):** desired speed, max acceleration, comfortable deceleration (+ a minimum gap).
- **Pros:** trivial to code; trivial to explain; very stable; few parameters to justify.
- **Cons:** unrealistic motion — cars tend to reach target speed abruptly and can produce jerky, "stop-start" behaviour; the acceleration profile isn't smooth or physically natural; weaker link to the literature you cite; capacity/delay numbers are less trustworthy in absolute terms (though your goal is *comparison*, not absolute prediction, which softens this).

### 6.2 Option B — Intelligent Driver Model (IDM)

The model from **Treiber & Kesting (2010)** — the very paper your proposal names as its inspiration. It computes a smooth, continuous acceleration in one equation:

```
a = a_max * [ 1 − (v / v0)^δ − (s* / s)² ]

    where the desired gap  s* = s0 + max(0,  v·T + v·Δv / (2·√(a_max·b)) )
```

Reading the equation (this is the intuition you'd give an examiner):

- `v` current speed, `v0` desired (free-flow) speed. The term `(v/v0)^δ` is the **"free road"** part: when far from anyone, it accelerates you toward `v0` and fades out as you approach it.
- `s` is the actual gap to the leader; `s*` is the gap you *want*. The term `(s*/s)²` is the **"interaction"** part: when your real gap `s` shrinks below your desired gap `s*`, this term grows fast and brakes you.
- `s*` grows with your speed (`v·T`, where `T` is your safe time-headway) and with your closing speed `Δv` — so you want more room when going fast or approaching a slower car.
- `s0` is the standstill gap (bumper-to-bumper spacing in a jam); `a_max` max accel; `b` comfortable braking; `δ` an exponent (usually 4).

- **Parameters (≈6):** `v0, T, a_max, b, s0, δ` — all with standard literature values (Treiber & Kesting publish typical sets), which is perfect since your data is synthetic and literature-derived by design.
- **Pros:** smooth, realistic, **collision-free by construction**; handles free-flow, approaching, following, and stopping in *one* equation; directly traceable to the paper you cite (strong rigor claim); the de-facto standard in open-source microsimulation; the virtual-obstacle trick works beautifully with it (a red light is just a leader with speed 0).
- **Cons:** ~6 parameters to introduce and justify (but they're all physically meaningful and you take standard values); slightly more math to explain — which this document is designed to help you do.

### 6.3 Recommendation

**Use IDM.** Three reasons, in order of weight:

1. **Rigor and traceability.** Your DSR "research rigor" guideline says the artifact must be built on established theory, and you *already cite Treiber & Kesting (2010)* as the inspiration. IDM is that theory. Choosing it turns a citation into an implemented foundation — the strongest possible answer to "how is your model grounded?"
2. **It's barely more work.** The whole model is one function of a handful of inputs. The "simpler" option isn't meaningfully faster to build once the loop exists, and it costs you realism and defensibility.
3. **One model, all situations.** Because a stop line / red light is modelled as a stationary virtual leader, IDM handles *stopping* for free. The simplified model needs extra special-casing to stop smoothly, so its simplicity is partly an illusion.

The one honest caveat — more parameters — is exactly the "simplicity without simplism" tension your Chapter 2 names. IDM sits on the right side of it: every parameter earns its place and maps to something a driver actually does. We'll expose all six in the config with sensible literature defaults, so you get realism *and* configurability.

**If you'd prefer**, we can implement the model behind the same interface as either choice and even swap between them — but I recommend committing to IDM and moving on.

---

## 7. Component 4 — Output / metrics

**Responsibility:** measure the simulation so scenarios can be compared. This component *reads* state and *records* numbers; it never influences the traffic.

### 7.1 What we measure (and precise definitions — definitions matter in a thesis)

Your proposal commits to these; here is how each is operationalised:

- **Delay (per vehicle):** actual travel time through the corridor minus the free-flow travel time (time it *would* have taken at the speed limit with no other cars). Reported as mean delay.
- **Waiting time (per vehicle):** total seconds the vehicle spent at or near zero speed (stopped). Reported as mean.
- **Queue length:** number of vehicles stopped/slow on an approach, sampled every 1 s (your stated interval). Reported as both **maximum** and **time-average** queue.
- **Throughput:** vehicles that completed their trip through the corridor per unit time (e.g. vehicles/hour). The headline capacity number.
- **Number of stops (per vehicle):** how many times it had to stop. A good coordination indicator — a green wave should reduce stops.

### 7.2 How it's collected

- **Virtual detectors** at chosen points (stop lines, corridor entry/exit) that count and time vehicles passing — the same concept MovSim uses.
- **Per-second sampling** for queue lengths (time series).
- **Per-vehicle records** finalised when a vehicle leaves the network (its delay, waiting time, stop count).
- Everything is written to **CSV** at the end of a run: one summary row per scenario/run, plus optional time-series files for plots. CSV because it's trivial to load into your analysis (pandas/matplotlib) for Chapter 5 charts, and it's exactly MovSim's output philosophy.

**Why / defend it:** these five metrics are precisely the ones your Chapter 2.3 (queuing theory) and 2.5 (output parameters) identify — queue length, delay, waiting time, throughput — plus stop-count as a coordination-sensitive extra. Precise, written-down definitions are what let you claim the comparison is valid. Keeping this component read-only guarantees that measuring the system doesn't perturb it.

---

## 8. The simulation engine (the loop) — and why headless matters

The engine owns the clock and runs the tick sequence from Section 2. Two design points deserve emphasis because they underwrite two of your four evaluation criteria.

### 8.1 Deterministic randomness → **reliability**

All randomness (when vehicles arrive, which way they turn, per-driver desired speed) comes from **one seeded random-number generator** created from the config. Same seed ⇒ same sequence of "random" choices ⇒ identical results. Your reliability criterion ("consistent results across multiple runs with the same settings") becomes a thing you can *show*: run seed 42 five times, get five identical output files. Change the seed to see natural variation; average over many seeds for robust scenario comparisons.

### 8.2 Headless mode → **performance** (and fair comparison)

Because the engine doesn't depend on Pygame, you can run it with no window as fast as the CPU allows. That lets you:

- run all three scenarios (and many random seeds each) in a batch to gather statistics, and
- do so quickly, which is your "performance" criterion — plus it's how you'll generate the data behind your Chapter 5 charts.

When you *do* want to watch, the same engine runs with the Pygame viewer attached, stepped in real time. Watching is for demonstration and debugging (your "functionality" criterion — you can literally see vehicles queue and discharge); measuring is done headless.

### 8.3 Warm-up and duration

We discard the first N seconds ("warm-up") so metrics aren't polluted by the unrealistic empty-network start, then measure over a defined period. Standard practice; we'll pick the numbers together during calibration.

**Why / defend it:** the engine/visual split (principle 2) is what makes reliability and performance demonstrable instead of hand-waved, and it's the specific weakness in the Gandhi reference we're deliberately *not* inheriting. A seeded RNG is the standard, and only, honest way to make a stochastic simulation reproducible.

---

## 9. Configuration system

A single `Config` object (a Python dataclass, later loadable from a JSON/YAML file) holds every tunable value, grouped to mirror your Chapter 2.5 parameter families:

- **Demand / arrival:** arrival rate per entry, turning-movement probabilities, directional split, RNG seed.
- **Network geometry:** node positions, link lengths (= intersection spacing), speed limits, lanes.
- **Vehicle behaviour (IDM):** `v0, T, a_max, b, s0, δ`, vehicle length (with variation).
- **Control:** which control each node uses, plus its parameters (stop rules; or cycle/green/amber/red/phase-sequence/lost-time; or offsets for coordination).
- **Output / run:** time step `dt`, warm-up, run duration, sampling intervals, output paths.

A **scenario** is then just a named config (or a small override on a shared base config): `baseline`, `isolated_signal`, `coordinated`. Running the study = running the same engine over these three configs.

**Why / defend it:** this is your "configurability" criterion made concrete, and it enforces fair comparison — the three scenarios share one base config and differ only where the science says they should (the control block).

---

## 10. Visualisation layer (Pygame)

A thin viewer that, each frame, reads the engine's current state and draws it: roads as lines, intersections as boxes, vehicles as coloured rectangles (colour by speed or by stopped/moving), and signal heads as red/amber/green dots with optional countdown — much like the Gandhi reference, which is a good *visual* template. It sends **no** information back into the engine. Keyboard controls (pause, step, restart, maybe speed-up) aid demonstration.

**Why / defend it:** Pygame is your stated tool; a read-only viewer keeps the "watch it" and "measure it" paths from interfering. Seeing vehicles visibly queue at the stop and flow through a green wave is your most persuasive functionality demonstration for a non-technical (management) audience — one of your two communication targets.

---

## 11. How the design satisfies your four evaluation criteria

| Criterion | Where it's delivered |
|---|---|
| **Functionality** | Engine runs, generates vehicles, moves them via IDM, forms queues, switches signals, records metrics (Sections 2, 4, 5, 7); visually confirmable (Section 10). |
| **Configurability** | Single config object; scenarios are configs; every Chapter 2.5 parameter exposed (Section 9). |
| **Reliability** | Seeded deterministic RNG → identical repeated runs (Section 8.1). |
| **Performance** | Headless batch execution; metric changes recorded across control mechanisms (Sections 7, 8.2). |

**Why / defend it:** you can point at a component for every criterion, which is what a DSR evaluation demands.

---

## 12. Proposed repository structure

```
corridor-sim/
├── README.md
├── requirements.txt              # pygame, numpy, pandas, matplotlib
├── config/
│   ├── base.yaml                 # shared defaults
│   ├── baseline.yaml             # scenario 1 overrides
│   ├── isolated_signal.yaml      # scenario 2 overrides
│   └── coordinated.yaml          # scenario 3 overrides
├── src/
│   ├── config.py                 # Config dataclass + loader
│   ├── network/                  # Component 1: Node, Link, Lane, Network
│   ├── vehicle/                  # Component 2: Vehicle + car_following (IDM)
│   ├── control/                  # Component 3: StopControl, FixedTimeSignal, CoordinatedNetwork
│   ├── output/                   # Component 4: detectors, metrics, CSV writers
│   ├── engine.py                 # the fixed-step loop, RNG, warm-up
│   └── viz/                      # Pygame viewer (optional, read-only)
├── run.py                        # entry point: run a scenario, headless or visual
├── analysis/                     # notebooks/scripts for Chapter 5 charts
└── tests/                        # unit tests (car-following, controls, metrics)
```

The `src/` folders map one-to-one to your four components — so the code layout itself tells the DSR story. Tests exist from the start because your reliability/functionality criteria basically ask for them (e.g. "a lone car reaches exactly `v0`"; "a car stops before a red light and never overshoots the stop line").

**Why / defend it:** the folder structure is a physical restatement of your four-component methodology, which makes the artifact self-documenting for the "communication of research" guideline.

---

## 13. Proposed build sequence (our roadmap for coming sessions)

Ordered so that something runs early and each step is independently testable:

1. **Config + engine skeleton** — the clock, the loop, seeded RNG. Runs and does nothing yet.
2. **Network** — one straight link, then the full four-node corridor as data.
3. **Vehicle + IDM on one link** — spawn cars, watch them free-flow and follow each other. *First provable physics.* Add the Pygame viewer here so we can see it.
4. **Output on the simple case** — measure delay/throughput on the single link; confirm numbers are sane.
5. **StopControl** — the baseline four-way stop (Scenario 1). Full corridor now runs end-to-end.
6. **FixedTimeSignal** — Scenario 2.
7. **CoordinatedNetwork + offsets** — Scenario 3.
8. **Calibration + warm-up + batch runner** — pick parameter values, warm-up length, run duration; batch all scenarios × seeds.
9. **Analysis** — the comparison charts and tables for Chapter 5.

Each numbered step is roughly one working session and produces something you can run, see, and explain.

**Why / defend it:** this is the iterative DSR "search process" in practice — build the smallest thing that works, verify it, then add the next behaviour. It also front-loads the risky part (car-following physics) so problems surface early.

---

## 14. Open decisions (need your / your supervisor's input)

1. **Exact corridor topology.** Please confirm the order and rough spacing of the four intersections (my read: Signal A – 4-way stop – Signal B – Main-gate stop). If you can pace out or estimate the distances from the map, even rough metres, that sharpens the geometry.
2. **Which intersection changes across scenarios.** I've assumed the **main gate** is the one swapped (stop → isolated signal), while the upstream signals provide the coordination in Scenario 3. Confirm that matches your intent.
3. **Turning at intersections.** Version 1 treats turns as routing (a vehicle's pre-assigned route) on single-lane links, i.e. no physical turn lanes or lane-changing. Acceptable for your scope? (Your scope already excludes lane-change complexity, so I believe yes.)
4. **Multi-lane approaches.** Start single-lane per direction, add lanes later only if needed? (Recommended: yes, start single-lane.)
5. **Demand profile.** Constant arrival rate during a peak, or a rising/falling profile across the run? (Recommended: start constant, add a peak profile later.)

Answer these when convenient — none of them block us starting on the engine skeleton (step 1), which is independent of these choices.

---

*End of v1. Next session: your answers to Section 14, then we begin step 1 (config + engine skeleton), building and explaining it together.*

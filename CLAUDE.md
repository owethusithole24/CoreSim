# CoreSim — Corridor Traffic Microsimulation (Honours project)

> This file is the project's persistent memory. It is read automatically at the
> start of each Claude Code session. It summarises everything decided so far so
> work can continue without the original chat history.

## Project at a glance

- **Title:** Designing microsimulations for analysing traffic control alternatives on a small scale
- **Student:** Owethu Jazmene Sithole (41380525) · **Supervisor:** Prof Susan Campher
- **Module:** ITRI671 · **Degree:** BCom Hons Informatics with CS & Informatics (2026)
- **Institution:** North-West University, Potchefstroom campus
- **Key deadlines:** Empirical chapter ~17 Aug 2026 · Full docs 5 Oct · Final resubmission 19 Oct · Project day 26 Oct 2026
- **Research question:** *How to design a microsimulation for analysing traffic control alternatives along a corridor on a small scale?*

## What we are building

A **custom microscopic traffic simulation in Python + Pygame**, driven by
**synthetic data** (no field data collected), that models the NWU main-gate
corridor and compares three traffic-control scenarios. It is a proof-of-concept
and a low-cost, open-source alternative to commercial tools (VISSIM) and even
SUMO. Developed in VS Code, version-controlled on GitHub, released open-source.

### The corridor (confirm exact spacing with student)
A chain of four intersections. Current working read (see Open Decisions):
`Signal A — 4-way stop — Signal B — MAIN GATE 4-way stop`.
The main gate four-way stop is the primary subject; short spacing between the
signals is why coordination matters.

### The three scenarios (only the CONTROL differs; network + vehicles stay identical)
1. **Baseline** — unsignalised four-way stop (FCFS + gap acceptance).
2. **Isolated** — single fixed-time signal.
3. **Coordinated** — network of fixed-time signals sharing offsets (green wave).

## Key design decisions (locked unless noted)

- **Model class:** microscopic (individual vehicles). Justified in Chapter 2.
- **Car-following:** **IDM (Intelligent Driver Model)**, Treiber & Kesting (2010) —
  recommended and to be used. *Student to give final confirmation.* Rationale:
  it's the model the proposal already cites, one equation handles free-flow,
  following AND stopping (a red light / stop line is modelled as a stationary
  "virtual leader"), collision-free, standard, strong rigor claim. Simplified
  kinematic follow-the-leader was the alternative (fewer params, less realism).
- **Signals:** **fixed-time only** (not actuated/adaptive) — chosen for
  simplicity, cost, and comparability (Chapter 2.2).
- **Architecture:** four components — **network / vehicle / control / output** —
  plus a time-stepped engine, a config object, and a decoupled Pygame viewer.
- **Engine/visual split:** the simulation runs headless for fast batch metrics
  and attaches Pygame only to watch. This underwrites the *performance* and
  *reliability* criteria and is the key weakness we avoid inheriting from the
  Gandhi reference repo.
- **Determinism:** one seeded RNG → identical repeated runs (*reliability*).
- **Config over code:** every parameter in one config; a scenario is a config.

### Evaluation criteria (from Chapter 3.4)
functionality · configurability · reliability · performance.

### Metrics (precise definitions in architecture_design.md §7)
mean delay · mean waiting time · max & time-average queue length · throughput ·
number of stops.

### Parameter families (Chapter 2.5)
demand/arrival (arrival rate, turning probabilities, directional split, seed) ·
network geometry (link lengths = intersection spacing, speed limits, lanes) ·
vehicle behaviour / IDM (v0, T, a_max, b, s0, δ, length) · control (stop rules;
cycle/green/amber/red/phase-sequence/lost-time; offsets) · output/run (dt,
warm-up, duration, sampling intervals).

## Build roadmap (one step ≈ one session)
1. Config + engine skeleton (clock, loop, seeded RNG).
2. Network (one link → full four-node corridor as data).
3. Vehicle + IDM on one link (first provable physics) + attach Pygame viewer.
4. Output on the simple case (sanity-check delay/throughput).
5. StopControl — baseline four-way stop (Scenario 1); full corridor runs.
6. FixedTimeSignal — Scenario 2.
7. CoordinatedNetwork + offsets — Scenario 3.
8. Calibration + warm-up + batch runner.
9. Analysis — comparison charts/tables for the empirical chapter.

**Next action:** start step 1 (config + engine skeleton).

## Open decisions (need student/supervisor input — see architecture_design.md §14)
1. Confirm corridor topology & rough intersection spacing (metres).
2. Confirm the main gate is the intersection swapped across scenarios.
3. Turns modelled as routing on single-lane links (no lane-changing) — OK for scope?
4. Start single-lane per direction, add lanes only if needed?
5. Demand: start with a constant peak arrival rate, add a rising/falling profile later?

## Reference repositories (ideas only, not dependencies)
- **MovSim** (github.com/movsim/movsim) — Java. Our **model** reference: IDM,
  signals, detectors. Mine the equations/logic, reimplement in Python.
- **Basic-Traffic-Intersection-Simulation** (github.com/mihir-m-gandhi/…) —
  Pygame. Our **visual** reference only; lacks car-following, gap acceptance,
  metrics, and couples sim to rendering (which we deliberately avoid).

## Working style (important)
The student is doing this as their own Honours artifact and must be able to
**explain and defend every line and decision** (NWU study-leader agreement:
content must be the student's own work; follow NWU AI-use guidelines). So:
**write clear, well-commented code AND explain the reasoning as we go** —
teaching, not just delivering. Prefer incremental, reviewable steps.

The student prefers concise, direct communication with minimal fluff.

## Files in this folder
- `architecture_design.md` — full architecture (the authoritative design; read this first).
- `four_way_stop_queue_demo.py` — standalone queuing-theory teaching demo (a
  stepping stone, NOT the artifact; no car-following, no signals).
- `DEMO_README.md` — how to run the demo + presentation talking points.
- `CLAUDE.md` — this file.
- (Recommended to also drop the research proposal PDF here for full context.)

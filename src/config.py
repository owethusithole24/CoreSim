"""Config: the single object that holds every tunable parameter for one run.

architecture_design.md Section 9 groups parameters into five families —
demand, network geometry, vehicle/IDM, control, output/run. We add fields to
a family only once a component that actually reads them exists (principle 4,
"configuration over code" — but there's no point configuring something
nothing uses yet). Right now only the engine exists, so Config only carries
the output/run timing fields and the RNG seed. Network, vehicle, control and
demand fields join this class in later steps.
"""

from dataclasses import dataclass, field


@dataclass
class NodeSpec:
    """Data describing one intersection. §3.1: "the layout is data, not code."""

    name: str
    control: str  # "stop" | "signal" — a label only. The actual control
                  # OBJECT (StopControl / FixedTimeSignal) is built in step
                  # 5/6; the network doesn't need it to exist yet.


@dataclass
class LinkSpec:
    """Data describing one one-directional road segment between two nodes."""

    upstream: str          # a NodeSpec.name
    downstream: str        # a NodeSpec.name
    length_m: float
    speed_limit_kmh: float = 50.0  # placeholder — NWU campus limit not yet confirmed
    lanes: int = 1                 # v1: one lane per direction (open decisions #3/#4)


@dataclass
class NetworkConfig:
    nodes: list[NodeSpec]
    links: list[LinkSpec]


def nwu_corridor() -> NetworkConfig:
    """The real main-gate corridor, confirmed 2026-08-08 from the student's
    illustration: main_gate (stop) -- signal_b -- upstream_stop -- signal_a
    (farthest from the gate), matching architecture_design.md's presumed
    order read in reverse (gate-outward instead of outward-to-gate).

    Link lengths are PLACEHOLDERS. The illustration didn't carry exact
    distances, only relative spacing, so these three round numbers preserve
    that ordering (gate<->signal_b reads as the longest gap, down to
    upstream_stop<->signal_a as the shortest) without pretending to be a
    measurement. Replace with real paced/estimated metres (open decision #1
    in architecture_design.md §14) whenever they're available.
    """
    nodes = [
        NodeSpec(name="main_gate", control="stop"),
        NodeSpec(name="signal_b", control="signal"),
        NodeSpec(name="upstream_stop", control="stop"),
        NodeSpec(name="signal_a", control="signal"),
    ]
    segments = [
        ("main_gate", "signal_b", 160.0),
        ("signal_b", "upstream_stop", 140.0),
        ("upstream_stop", "signal_a", 110.0),
    ]
    # a two-way road between two nodes is two links, one each way (§3.1)
    links = []
    for a, b, length_m in segments:
        links.append(LinkSpec(upstream=a, downstream=b, length_m=length_m))
        links.append(LinkSpec(upstream=b, downstream=a, length_m=length_m))
    return NetworkConfig(nodes=nodes, links=links)


@dataclass
class Config:
    # --- output/run family (architecture_design.md §9) ---
    dt: float = 0.1          # simulation time step, seconds
    warmup_s: float = 0.0    # discarded lead-in before metrics count, seconds (§8.3)
    duration_s: float = 60.0 # simulated seconds to run *after* warm-up

    # --- network geometry family (§9) ---
    network: NetworkConfig = field(default_factory=nwu_corridor)

    # --- shared across all families: the one seed everything derives from (§8.1) ---
    seed: int = 42

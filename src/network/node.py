"""Node: an intersection — a point where roads meet (architecture_design.md §3.1)."""

from dataclasses import dataclass


@dataclass
class Node:
    name: str
    # The control OBJECT (StopControl / FixedTimeSignal) attaches here in
    # step 5/6 — a Node just needs the slot to exist, not the behaviour yet.
    control: object = None

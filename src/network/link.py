"""Link: a one-directional road segment connecting two nodes (§3.1).

A vehicle lives "on" a link at some position measured in metres from its
start (§4.1). A two-way road between two intersections is two Links, one
each way — the corridor builder in network.py creates both.
"""

from dataclasses import dataclass

from src.network.node import Node


@dataclass
class Link:
    name: str
    upstream: Node    # where the link starts
    downstream: Node  # where the link ends
    length_m: float
    speed_limit_kmh: float = 50.0
    lanes: int = 1  # v1: one lane per direction, turning is routing not
                     # lane-changing (open decisions #3/#4)

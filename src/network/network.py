"""Network / Corridor: the container holding all nodes and links, and knowing
how they connect (§3.1). Holds geometry and topology, nothing that moves.
"""

from dataclasses import dataclass

from src.config import NetworkConfig
from src.network.link import Link
from src.network.node import Node


@dataclass
class Network:
    nodes: dict[str, Node]
    links: dict[str, Link]

    def node(self, name: str) -> Node:
        return self.nodes[name]

    def link(self, name: str) -> Link:
        return self.links[name]

    def links_from(self, node_name: str) -> list[Link]:
        """Every link that starts at this node — what a vehicle there can take next."""
        return [l for l in self.links.values() if l.upstream.name == node_name]


def build_network(network_config: NetworkConfig) -> Network:
    """Turn the plain-data NetworkConfig (§3.2: "the layout is data, not
    code") into live Node/Link objects the rest of the engine can use.
    """
    nodes = {spec.name: Node(name=spec.name) for spec in network_config.nodes}

    links = {}
    for spec in network_config.links:
        name = f"{spec.upstream}_to_{spec.downstream}"
        links[name] = Link(
            name=name,
            upstream=nodes[spec.upstream],
            downstream=nodes[spec.downstream],
            length_m=spec.length_m,
            speed_limit_kmh=spec.speed_limit_kmh,
            lanes=spec.lanes,
        )

    return Network(nodes=nodes, links=links)

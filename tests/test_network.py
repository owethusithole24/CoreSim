"""Tests for the network component: generic Node/Link/Network mechanics on a
minimal synthetic spec, then the real NWU corridor built from config data.
"""

from src.config import LinkSpec, NetworkConfig, NodeSpec, nwu_corridor
from src.network import build_network


def test_build_network_from_a_minimal_synthetic_spec():
    config = NetworkConfig(
        nodes=[NodeSpec(name="a", control="stop"), NodeSpec(name="b", control="stop")],
        links=[LinkSpec(upstream="a", downstream="b", length_m=100.0)],
    )
    network = build_network(config)

    assert set(network.nodes) == {"a", "b"}
    link = network.link("a_to_b")
    assert link.upstream.name == "a"
    assert link.downstream.name == "b"
    assert link.length_m == 100.0


def test_links_from_finds_only_outgoing_links():
    config = NetworkConfig(
        nodes=[NodeSpec(name="a", control="stop"), NodeSpec(name="b", control="stop")],
        links=[
            LinkSpec(upstream="a", downstream="b", length_m=100.0),
            LinkSpec(upstream="b", downstream="a", length_m=100.0),
        ],
    )
    network = build_network(config)

    outgoing = network.links_from("a")
    assert len(outgoing) == 1
    assert outgoing[0].downstream.name == "b"


def test_nwu_corridor_has_four_nodes():
    network = build_network(nwu_corridor())
    assert set(network.nodes) == {"main_gate", "signal_b", "upstream_stop", "signal_a"}


def test_nwu_corridor_is_fully_connected_both_directions():
    network = build_network(nwu_corridor())

    # a 4-node chain, two-way: the two end nodes have 1 outgoing link each,
    # the two interior nodes have 2 (one toward each neighbour).
    assert len(network.links_from("main_gate")) == 1
    assert len(network.links_from("signal_b")) == 2
    assert len(network.links_from("upstream_stop")) == 2
    assert len(network.links_from("signal_a")) == 1
    assert len(network.links) == 6


def test_nwu_corridor_link_lengths_preserve_relative_ordering_from_sketch():
    network = build_network(nwu_corridor())

    gate_to_b = network.link("main_gate_to_signal_b").length_m
    b_to_stop = network.link("signal_b_to_upstream_stop").length_m
    stop_to_a = network.link("upstream_stop_to_signal_a").length_m

    assert gate_to_b > b_to_stop > stop_to_a

"""Tests for the IDM equation itself, in isolation from Vehicle objects —
just numbers in, a number out. Sign and magnitude checks that pin down the
physical intuition from architecture_design.md §6.2.
"""

from src.config import IDMConfig
from src.vehicle.idm import idm_acceleration


def test_stationary_on_a_clear_road_accelerates_at_a_max():
    idm = IDMConfig()
    a = idm_acceleration(speed=0.0, gap=None, closing_speed=0.0, idm=idm)
    assert a == idm.a_max


def test_at_desired_speed_on_a_clear_road_acceleration_is_zero():
    idm = IDMConfig()
    a = idm_acceleration(speed=idm.v0, gap=None, closing_speed=0.0, idm=idm)
    assert abs(a) < 1e-9


def test_above_desired_speed_on_a_clear_road_decelerates():
    idm = IDMConfig()
    a = idm_acceleration(speed=idm.v0 * 1.2, gap=None, closing_speed=0.0, idm=idm)
    assert a < 0


def test_tiny_gap_to_a_matching_speed_leader_brakes_hard():
    idm = IDMConfig()
    # gap far smaller than the desired gap at this speed -> strong braking
    a = idm_acceleration(speed=10.0, gap=0.5, closing_speed=0.0, idm=idm)
    assert a < -idm.a_max  # braking harder than it would ever accelerate


def test_very_large_gap_behaves_like_a_clear_road():
    idm = IDMConfig()
    free_road_a = idm_acceleration(speed=5.0, gap=None, closing_speed=0.0, idm=idm)
    huge_gap_a = idm_acceleration(speed=5.0, gap=10_000.0, closing_speed=0.0, idm=idm)
    assert abs(free_road_a - huge_gap_a) < 1e-6


def test_closing_fast_on_a_slower_leader_brakes_more_than_matching_speed():
    idm = IDMConfig()
    matching = idm_acceleration(speed=10.0, gap=15.0, closing_speed=0.0, idm=idm)
    closing_fast = idm_acceleration(speed=10.0, gap=15.0, closing_speed=8.0, idm=idm)
    assert closing_fast < matching

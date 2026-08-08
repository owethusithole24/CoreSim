"""Tests for the engine skeleton.

These exist from step 1 because two of the four evaluation criteria
(reliability, functionality — architecture_design.md §11) are claims we need
to be able to *show*, not just assert in the report. A test that runs the
same seed twice and diffs the result is that proof in miniature.
"""

from src.config import Config
from src.engine import Engine


def test_clock_advances_by_dt_each_step():
    engine = Engine(Config(dt=0.1, duration_s=1.0, seed=1))
    engine.step()
    assert engine.tick == 1
    assert round(engine.t, 8) == 0.1


def test_run_stops_at_duration():
    engine = Engine(Config(dt=0.1, duration_s=1.0, seed=1))
    engine.run()
    assert engine.tick == 10
    assert round(engine.t, 8) == 1.0


def test_run_includes_warmup_in_total_time():
    engine = Engine(Config(dt=0.1, duration_s=1.0, warmup_s=0.5, seed=1))
    engine.run()
    assert round(engine.t, 8) == 1.5


def test_warmup_flag_flips_at_the_boundary():
    engine = Engine(Config(dt=0.1, duration_s=1.0, warmup_s=0.5, seed=1))
    assert not engine.is_warmed_up
    for _ in range(5):
        engine.step()
    assert round(engine.t, 8) == 0.5
    assert engine.is_warmed_up


def test_same_seed_produces_identical_rng_sequence():
    a = Engine(Config(seed=7))
    b = Engine(Config(seed=7))
    draws_a = [a.rng.random() for _ in range(20)]
    draws_b = [b.rng.random() for _ in range(20)]
    assert draws_a == draws_b


def test_different_seed_produces_a_different_rng_sequence():
    a = Engine(Config(seed=1))
    b = Engine(Config(seed=2))
    assert a.rng.random() != b.rng.random()

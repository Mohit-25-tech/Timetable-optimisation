import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.data.sample_data import build_sample_dataset
from backend.models.schemas import GAConfig
from backend.optimizer.chromosome import ProblemContext, Gene
from backend.optimizer.fitness import evaluate


def test_fitness_is_inverse_of_cost():
    ds = build_sample_dataset()
    ctx = ProblemContext.build(ds)
    cfg = GAConfig()
    chromo = [Gene(ds.subjects[0].subject_id, "F01", "B1", ds.rooms[0].room_id, "Mon", 1)]
    cost, fitness, _ = evaluate(chromo, ctx, cfg)
    assert fitness == 1.0 / (1.0 + cost)


def test_lower_cost_conflicting_schedule_has_lower_fitness():
    ds = build_sample_dataset()
    ctx = ProblemContext.build(ds)
    cfg = GAConfig()

    clean = [
        Gene(ds.subjects[0].subject_id, "F01", "B1", ds.rooms[0].room_id, "Mon", 1),
        Gene(ds.subjects[1].subject_id, "F02", "B2", ds.rooms[1].room_id, "Mon", 2),
    ]
    conflicted = [
        Gene(ds.subjects[0].subject_id, "F01", "B1", ds.rooms[0].room_id, "Mon", 1),
        Gene(ds.subjects[1].subject_id, "F01", "B2", ds.rooms[0].room_id, "Mon", 1),
    ]

    clean_cost, clean_fit, _ = evaluate(clean, ctx, cfg)
    bad_cost, bad_fit, _ = evaluate(conflicted, ctx, cfg)

    assert bad_cost > clean_cost
    assert bad_fit < clean_fit


def test_hard_weights_dominate_soft_weights():
    cfg = GAConfig()
    assert cfg.hard_faculty_conflict > cfg.faculty_gap * 10
    assert cfg.hard_room_conflict > cfg.distribution_penalty * 10

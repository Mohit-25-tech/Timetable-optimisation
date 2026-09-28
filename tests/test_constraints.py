import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.data.sample_data import build_sample_dataset
from backend.models.schemas import GAConfig
from backend.optimizer.chromosome import ProblemContext, Gene
from backend.optimizer.fitness import evaluate


def _ctx():
    ds = build_sample_dataset()
    return ds, ProblemContext.build(ds)


def test_faculty_conflict_detected():
    ds, ctx = _ctx()
    cfg = GAConfig()
    s1, s2 = ds.subjects[0], ds.subjects[1]
    # Force the same faculty into two classes at the same day/period.
    chromo = [
        Gene(s1.subject_id, "F01", s1.batch_id, ds.rooms[0].room_id, "Mon", 1),
        Gene(s2.subject_id, "F01", s2.batch_id, ds.rooms[1].room_id, "Mon", 1),
    ]
    _, _, counts = evaluate(chromo, ctx, cfg)
    assert counts.faculty_conflicts == 1


def test_room_conflict_detected():
    ds, ctx = _ctx()
    cfg = GAConfig()
    s1, s2 = ds.subjects[0], ds.subjects[1]
    chromo = [
        Gene(s1.subject_id, "F01", s1.batch_id, "R01", "Mon", 1),
        Gene(s2.subject_id, "F02", s2.batch_id, "R01", "Mon", 1),
    ]
    _, _, counts = evaluate(chromo, ctx, cfg)
    assert counts.room_conflicts == 1


def test_batch_conflict_detected():
    ds, ctx = _ctx()
    cfg = GAConfig()
    s1, s2 = ds.subjects[0], ds.subjects[1]
    chromo = [
        Gene(s1.subject_id, "F01", "B1", ds.rooms[0].room_id, "Mon", 1),
        Gene(s2.subject_id, "F02", "B1", ds.rooms[1].room_id, "Mon", 1),
    ]
    _, _, counts = evaluate(chromo, ctx, cfg)
    assert counts.student_conflicts == 1


def test_capacity_violation_detected():
    ds, ctx = _ctx()
    cfg = GAConfig()
    small_room = min(ds.rooms, key=lambda r: r.capacity)
    big_batch = max(ds.batches, key=lambda b: b.student_count)
    assert small_room.capacity < big_batch.student_count
    chromo = [Gene(ds.subjects[0].subject_id, "F01", big_batch.batch_id, small_room.room_id, "Mon", 1)]
    _, _, counts = evaluate(chromo, ctx, cfg)
    assert counts.capacity_violations == 1


def test_no_conflicts_for_clean_schedule():
    ds, ctx = _ctx()
    cfg = GAConfig()
    big_room_1, big_room_2 = sorted(ds.rooms, key=lambda r: -r.capacity)[:2]
    chromo = [
        Gene(ds.subjects[0].subject_id, "F01", "B1", big_room_1.room_id, "Mon", 1),
        Gene(ds.subjects[1].subject_id, "F02", "B2", big_room_2.room_id, "Mon", 1),
    ]
    _, _, counts = evaluate(chromo, ctx, cfg)
    assert counts.hard_total == 0

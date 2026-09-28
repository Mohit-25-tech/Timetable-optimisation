import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import random

from backend.data.sample_data import build_sample_dataset
from backend.models.schemas import GAConfig
from backend.optimizer.chromosome import ProblemContext, create_initial_population
from backend.optimizer.operators import tournament_selection, two_point_crossover, mutate, repair
from backend.optimizer.fitness import evaluate
from backend.optimizer.ga import run_ga


def _ctx():
    ds = build_sample_dataset()
    return ds, ProblemContext.build(ds)


def test_initial_population_has_all_required_sessions():
    ds, ctx = _ctx()
    pop = create_initial_population(ctx, 5, random.Random(0))
    expected = sum(s.sessions_per_week for s in ds.subjects)
    for chromo in pop:
        assert len(chromo) == expected


def test_crossover_preserves_chromosome_length_and_gene_identity():
    ds, ctx = _ctx()
    rng = random.Random(1)
    pop = create_initial_population(ctx, 2, rng)
    a, b = two_point_crossover(pop[0], pop[1], rng)
    assert len(a) == len(pop[0])
    assert len(b) == len(pop[1])
    # subject/faculty/batch identity (the curriculum requirement) is unchanged by crossover
    assert [g.subject_id for g in a] == [g.subject_id for g in pop[0]]


def test_mutation_changes_at_least_one_gene_with_high_rate():
    ds, ctx = _ctx()
    rng = random.Random(2)
    pop = create_initial_population(ctx, 1, rng)
    original = [(g.day, g.period, g.room_id) for g in pop[0]]
    mutate(pop[0], ctx, mutation_rate=1.0, rng=rng)
    mutated = [(g.day, g.period, g.room_id) for g in pop[0]]
    assert original != mutated


def test_repair_reduces_or_eliminates_hard_violations():
    ds, ctx = _ctx()
    cfg = GAConfig()
    rng = random.Random(3)
    pop = create_initial_population(ctx, 1, rng)
    chromo = pop[0]
    # Force conflicts by collapsing everything onto one day/period.
    for g in chromo:
        g.day, g.period = "Mon", 1
    _, _, before = evaluate(chromo, ctx, cfg)
    for _ in range(5):
        repair(chromo, ctx, rng)
    _, _, after = evaluate(chromo, ctx, cfg)
    assert after.hard_total <= before.hard_total


def test_tournament_selection_returns_valid_chromosome():
    ds, ctx = _ctx()
    cfg = GAConfig()
    rng = random.Random(4)
    pop = create_initial_population(ctx, 6, rng)
    fitnesses = [evaluate(c, ctx, cfg)[1] for c in pop]
    selected = tournament_selection(pop, fitnesses, tournament_size=3, rng=rng)
    assert len(selected) == len(pop[0])


def test_ga_execution_reduces_cost_over_generations():
    ds = build_sample_dataset()
    cfg = GAConfig(population_size=30, generations=25, random_seed=7, stagnation_limit=50)
    result = run_ga(ds, cfg)
    assert result.history[0].best_cost >= result.history[-1].best_cost
    assert result.generations_executed <= cfg.generations
    assert len(result.best_chromosome) == sum(s.sessions_per_week for s in ds.subjects)


def test_ga_can_reach_zero_hard_violations_on_demo_dataset():
    ds = build_sample_dataset()
    cfg = GAConfig(population_size=60, generations=120, random_seed=42, stagnation_limit=40)
    result = run_ga(ds, cfg)
    assert result.best_counts.hard_total == 0


def test_api_optimize_response_is_valid():
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    demo = client.get("/api/demo-data").json()
    payload = {"dataset": demo, "config": {"population_size": 30, "generations": 20, "random_seed": 5, "stagnation_limit": 10}}
    r = client.post("/api/optimize", json=payload)
    assert r.status_code == 200
    data = r.json()
    expected_sessions = sum(s["sessions_per_week"] for s in demo["subjects"])
    assert len(data["timetable"]) == expected_sessions
    assert len(data["history"]) == data["generations_executed"]

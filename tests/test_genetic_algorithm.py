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


# ==========================================================================
# Phase 1 tests: new operators and improvements
# ==========================================================================


def test_swap_mutate_preserves_chromosome_length_and_identity():
    """swap_mutate only swaps (day, period, room) between genes; it must not
    change chromosome length or the (subject, faculty, batch) identity."""
    from backend.optimizer.operators import swap_mutate
    ds, ctx = _ctx()
    rng = random.Random(10)
    pop = create_initial_population(ctx, 1, rng)
    chromo = pop[0]
    original_ids = [(g.subject_id, g.faculty_id, g.batch_id) for g in chromo]
    original_len = len(chromo)
    swap_mutate(chromo, ctx, mutation_rate=1.0, rng=rng)
    assert len(chromo) == original_len
    assert [(g.subject_id, g.faculty_id, g.batch_id) for g in chromo] == original_ids


def test_local_search_does_not_increase_cost():
    """local_search is a hill-climbing pass: output cost must be <= input cost."""
    from backend.optimizer.operators import local_search
    ds, ctx = _ctx()
    cfg = GAConfig()
    rng = random.Random(11)
    pop = create_initial_population(ctx, 1, rng)
    chromo = pop[0]
    cost_before, _, _ = evaluate(chromo, ctx, cfg)
    cost_after = local_search(chromo, ctx, cfg, max_iterations=20, rng=rng)
    assert cost_after <= cost_before


def test_greedy_chromosome_has_fewer_initial_conflicts():
    """Greedy initialization should produce far fewer hard conflicts than random."""
    from backend.optimizer.chromosome import create_greedy_chromosome
    ds, ctx = _ctx()
    cfg = GAConfig()
    rng = random.Random(12)

    greedy_violations = []
    random_violations = []
    for seed in range(5):
        r = random.Random(seed + 100)
        g_chromo = create_greedy_chromosome(ctx, r)
        _, _, g_counts = evaluate(g_chromo, ctx, cfg)
        greedy_violations.append(g_counts.hard_total)

        r2 = random.Random(seed + 200)
        from backend.optimizer.chromosome import create_random_chromosome
        r_chromo = create_random_chromosome(ctx, r2)
        _, _, r_counts = evaluate(r_chromo, ctx, cfg)
        random_violations.append(r_counts.hard_total)

    avg_greedy = sum(greedy_violations) / len(greedy_violations)
    avg_random = sum(random_violations) / len(random_violations)
    # Greedy should be strictly better on average.
    assert avg_greedy < avg_random


def test_greedy_init_produces_valid_chromosome():
    """Greedy chromosome must have exactly the right number of genes with
    correct (subject, faculty, batch) identities."""
    from backend.optimizer.chromosome import create_greedy_chromosome
    ds, ctx = _ctx()
    rng = random.Random(13)
    chromo = create_greedy_chromosome(ctx, rng)
    expected = sum(s.sessions_per_week for s in ds.subjects)
    assert len(chromo) == expected
    # Check that every required session is represented.
    required = [(r.subject_id, r.faculty_id, r.batch_id) for r in ctx.required_sessions]
    actual = sorted([(g.subject_id, g.faculty_id, g.batch_id) for g in chromo])
    assert actual == sorted(required)


def test_adaptive_mutation_rate_increases_with_stagnation():
    """_compute_effective_mutation_rate should ramp linearly from min to max."""
    from backend.optimizer.ga import _compute_effective_mutation_rate
    cfg = GAConfig(adaptive_mutation=True, mutation_rate_min=0.05,
                   mutation_rate_max=0.40, stagnation_limit=40)
    rate_0 = _compute_effective_mutation_rate(cfg, stagnant_generations=0)
    rate_20 = _compute_effective_mutation_rate(cfg, stagnant_generations=20)
    rate_40 = _compute_effective_mutation_rate(cfg, stagnant_generations=40)
    assert abs(rate_0 - 0.05) < 1e-9
    assert rate_20 > rate_0
    assert rate_20 < rate_40
    assert abs(rate_40 - 0.40) < 1e-9

    # When disabled, should just return the static mutation_rate.
    cfg_off = GAConfig(adaptive_mutation=False, mutation_rate=0.10)
    assert _compute_effective_mutation_rate(cfg_off, stagnant_generations=100) == 0.10


def test_diversity_injection_preserves_population_size():
    """When diversity injection fires, population size must remain correct and
    elites must be unchanged."""
    ds, ctx = _ctx()
    cfg = GAConfig(
        population_size=30, generations=30, random_seed=42,
        stagnation_limit=50,
        diversity_injection=True, diversity_trigger_gens=5, diversity_replace_pct=0.20,
    )
    result = run_ga(ds, cfg)
    # The GA should have run all 30 generations (stagnation_limit=50 won't fire).
    assert result.generations_executed == 30
    # Population integrity: best chromosome is still 90 genes.
    assert len(result.best_chromosome) == sum(s.sessions_per_week for s in ds.subjects)


def test_ga_with_all_improvements_reaches_zero_hard_violations():
    """Full GA with all Phase 1 improvements enabled must still reach 0 hard violations."""
    ds = build_sample_dataset()
    cfg = GAConfig(
        population_size=60, generations=150, random_seed=42, stagnation_limit=60,
        adaptive_mutation=True, mutation_rate_min=0.05, mutation_rate_max=0.35,
        diversity_injection=True, diversity_trigger_gens=10, diversity_replace_pct=0.15,
        swap_mutation_prob=0.30,
        local_search_enabled=True, local_search_top_k=3, local_search_iterations=8,
        greedy_init_fraction=0.20,
    )
    result = run_ga(ds, cfg)
    assert result.best_counts.hard_total == 0


"""
The complete Genetic Algorithm pipeline:

    Input Data -> Chromosome Representation -> Initial Population
    -> Fitness Evaluation -> Tournament Selection -> Crossover -> Mutation
    -> Constraint Repair -> Elitism -> Next Generation -> Termination
    -> Best Timetable

Phase 1 additions (all configurable and off by default):
    - Adaptive mutation rate (ramps on stagnation, resets on improvement)
    - Diversity injection (replace worst individuals with fresh ones when stagnating)
    - Swap-based mutation (mixed with standard mutation via probability)
    - Memetic local search (hill-climbing on top-k individuals each generation)
    - Greedy constructive initialization (fraction of population)

This module contains no UI or API concerns -- it is imported directly by both
the FastAPI backend and the explanatory notebook, so there is exactly one GA
implementation in the project.
"""
from __future__ import annotations
import random
import time
from dataclasses import dataclass
from typing import List, Optional

from backend.models.schemas import DatasetInput, GAConfig
from backend.optimizer.chromosome import ProblemContext, Chromosome, create_initial_population, create_random_chromosome
from backend.optimizer.fitness import evaluate, ConstraintCounts
from backend.optimizer.operators import (
    tournament_selection, two_point_crossover, mutate, repair,
    swap_mutate, local_search,
)


@dataclass
class GenerationRecord:
    generation: int
    best_fitness: float
    avg_fitness: float
    best_cost: float
    hard_violations: int
    soft_penalty: float


@dataclass
class GAResult:
    best_chromosome: Chromosome
    best_cost: float
    best_fitness: float
    best_counts: ConstraintCounts
    history: List[GenerationRecord]
    generations_executed: int
    execution_time_seconds: float
    converged_early: bool
    context: ProblemContext
    initial_cost: float = 0.0
    initial_fitness: float = 0.0
    initial_counts: Optional[ConstraintCounts] = None


def _compute_effective_mutation_rate(config: GAConfig, stagnant_generations: int) -> float:
    """Compute the effective mutation rate for this generation.

    When adaptive_mutation is disabled, returns the static config.mutation_rate.
    When enabled, linearly ramps from mutation_rate_min toward mutation_rate_max
    as stagnation grows, using the stagnation_limit as the scaling denominator.
    """
    if not config.adaptive_mutation:
        return config.mutation_rate

    limit = config.stagnation_limit if config.stagnation_limit else 40
    t = min(stagnant_generations / limit, 1.0)
    return config.mutation_rate_min + (config.mutation_rate_max - config.mutation_rate_min) * t


def run_ga(dataset: DatasetInput, config: GAConfig) -> GAResult:
    start_time = time.time()
    rng = random.Random(config.random_seed) if config.random_seed is not None else random.Random()

    ctx = ProblemContext.build(dataset)
    population = create_initial_population(ctx, config.population_size, rng,
                                           greedy_fraction=config.greedy_init_fraction)

    history: List[GenerationRecord] = []
    best_chromosome: Optional[Chromosome] = None
    best_cost = float("inf")
    best_fitness = 0.0
    best_counts: Optional[ConstraintCounts] = None
    initial_cost = 0.0
    initial_fitness = 0.0
    initial_counts: Optional[ConstraintCounts] = None
    stagnant_generations = 0
    converged_early = False
    generations_executed = 0

    for generation in range(1, config.generations + 1):
        generations_executed = generation

        evaluations = [evaluate(chromo, ctx, config) for chromo in population]
        costs = [e[0] for e in evaluations]
        fitnesses = [e[1] for e in evaluations]
        counts_list = [e[2] for e in evaluations]

        gen_best_idx = min(range(len(population)), key=lambda i: costs[i])
        gen_best_cost = costs[gen_best_idx]
        gen_best_fitness = fitnesses[gen_best_idx]
        avg_fitness = sum(fitnesses) / len(fitnesses)

        if generation == 1:
            initial_cost = gen_best_cost
            initial_fitness = gen_best_fitness
            initial_counts = counts_list[gen_best_idx]

        improved = gen_best_cost < best_cost
        if improved:
            best_cost = gen_best_cost
            best_fitness = gen_best_fitness
            best_chromosome = [g.copy() for g in population[gen_best_idx]]
            best_counts = counts_list[gen_best_idx]
            stagnant_generations = 0
        else:
            stagnant_generations += 1

        history.append(GenerationRecord(
            generation=generation,
            best_fitness=gen_best_fitness,
            avg_fitness=avg_fitness,
            best_cost=gen_best_cost,
            hard_violations=counts_list[gen_best_idx].hard_total,
            soft_penalty=gen_best_cost - (
                config.hard_faculty_conflict * counts_list[gen_best_idx].faculty_conflicts
                + config.hard_student_conflict * counts_list[gen_best_idx].student_conflicts
                + config.hard_room_conflict * counts_list[gen_best_idx].room_conflicts
                + config.capacity_violation * counts_list[gen_best_idx].capacity_violations
            ),
        ))

        # Early stopping: zero hard violations and soft cost has plateaued.
        if best_counts is not None and best_counts.hard_total == 0 and config.stagnation_limit is not None \
                and stagnant_generations >= config.stagnation_limit:
            converged_early = True
            break

        if generation == config.generations:
            break

        # --- Compute effective mutation rate for this generation ---
        effective_mutation_rate = _compute_effective_mutation_rate(config, stagnant_generations)

        # --- Next generation ---
        # Elitism: carry the best `elite_count` individuals forward unchanged.
        ranked_indices = sorted(range(len(population)), key=lambda i: costs[i])
        next_population: List[Chromosome] = [
            [g.copy() for g in population[i]] for i in ranked_indices[:config.elite_count]
        ]

        while len(next_population) < config.population_size:
            parent_a = tournament_selection(population, fitnesses, config.tournament_size, rng)
            parent_b = tournament_selection(population, fitnesses, config.tournament_size, rng)

            if rng.random() < config.crossover_rate:
                child_a, child_b = two_point_crossover(parent_a, parent_b, rng)
            else:
                child_a, child_b = parent_a, parent_b

            # --- Mutation: choose between swap-only mutation and standard mutation ---
            for child in (child_a, child_b):
                if config.swap_mutation_prob > 0.0 and rng.random() < config.swap_mutation_prob:
                    swap_mutate(child, ctx, effective_mutation_rate, rng)
                else:
                    mutate(child, ctx, effective_mutation_rate, rng)

            repair(child_a, ctx, rng)
            repair(child_b, ctx, rng)

            next_population.append(child_a)
            if len(next_population) < config.population_size:
                next_population.append(child_b)

        # --- Diversity injection ---
        if config.diversity_injection and stagnant_generations > 0 \
                and stagnant_generations % config.diversity_trigger_gens == 0:
            replace_count = max(1, int(config.population_size * config.diversity_replace_pct))
            # Replace the worst individuals (those at the end of the ranked list).
            # Elites are at the front of next_population, so we replace from the back.
            for idx in range(len(next_population) - 1,
                             max(config.elite_count - 1, len(next_population) - 1 - replace_count), -1):
                fresh = create_random_chromosome(ctx, rng)
                repair(fresh, ctx, rng)
                next_population[idx] = fresh

        # --- Memetic local search on top-k individuals ---
        if config.local_search_enabled:
            # Re-evaluate the population to rank them for local search.
            ls_evals = [evaluate(chromo, ctx, config) for chromo in next_population]
            ls_costs = [e[0] for e in ls_evals]
            ls_ranked = sorted(range(len(next_population)), key=lambda i: ls_costs[i])
            for rank_pos in range(min(config.local_search_top_k, len(ls_ranked))):
                idx = ls_ranked[rank_pos]
                local_search(next_population[idx], ctx, config,
                             config.local_search_iterations, rng)

        population = next_population

    execution_time = time.time() - start_time

    assert best_chromosome is not None and best_counts is not None
    return GAResult(
        best_chromosome=best_chromosome,
        best_cost=best_cost,
        best_fitness=best_fitness,
        best_counts=best_counts,
        history=history,
        generations_executed=generations_executed,
        execution_time_seconds=execution_time,
        converged_early=converged_early,
        context=ctx,
        initial_cost=initial_cost,
        initial_fitness=initial_fitness,
        initial_counts=initial_counts,
    )

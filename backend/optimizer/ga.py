"""
The complete Genetic Algorithm pipeline:

    Input Data -> Chromosome Representation -> Initial Population
    -> Fitness Evaluation -> Tournament Selection -> Crossover -> Mutation
    -> Constraint Repair -> Elitism -> Next Generation -> Termination
    -> Best Timetable

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
from backend.optimizer.chromosome import ProblemContext, Chromosome, create_initial_population
from backend.optimizer.fitness import evaluate, ConstraintCounts
from backend.optimizer.operators import tournament_selection, two_point_crossover, mutate, repair


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


def run_ga(dataset: DatasetInput, config: GAConfig) -> GAResult:
    start_time = time.time()
    rng = random.Random(config.random_seed) if config.random_seed is not None else random.Random()

    ctx = ProblemContext.build(dataset)
    population = create_initial_population(ctx, config.population_size, rng)

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

            mutate(child_a, ctx, config.mutation_rate, rng)
            mutate(child_b, ctx, config.mutation_rate, rng)

            repair(child_a, ctx, rng)
            repair(child_b, ctx, rng)

            next_population.append(child_a)
            if len(next_population) < config.population_size:
                next_population.append(child_b)

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

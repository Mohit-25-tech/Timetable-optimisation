"""
Genetic operators for the timetable GA.

Selection:   Tournament selection -- pick K random individuals, keep the fittest.
Crossover:   Two-point crossover over the flat gene list, followed by repair
             (crossover can create faculty/room/batch conflicts; repair fixes them).
Mutation:    Randomly changes a gene's day/period, room, or swaps two genes' slots.
Repair:      Bounded-attempt local search that reassigns a conflicting gene to a
             feasible slot; anything it can't fix in the attempt budget is left
             for the fitness function to penalize.
"""
from __future__ import annotations
import random
from collections import defaultdict
from typing import List, Tuple

from backend.optimizer.chromosome import Chromosome, Gene, ProblemContext


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def tournament_selection(population: List[Chromosome], fitnesses: List[float],
                          tournament_size: int, rng: random.Random) -> Chromosome:
    """Randomly sample `tournament_size` individuals, return a copy of the fittest."""
    contenders = rng.sample(range(len(population)), min(tournament_size, len(population)))
    best_idx = max(contenders, key=lambda i: fitnesses[i])
    return [g.copy() for g in population[best_idx]]


# ---------------------------------------------------------------------------
# Crossover
# ---------------------------------------------------------------------------

def two_point_crossover(parent_a: Chromosome, parent_b: Chromosome,
                         rng: random.Random) -> Tuple[Chromosome, Chromosome]:
    """Two-point crossover over the assignment list. Gene order is aligned
    (both chromosomes list the same required sessions in the same order), so
    we swap the (room, day, period) segment between two cut points -- the
    subject/faculty/batch identity of each gene never changes, only where it
    is scheduled. This keeps every required session present after crossover;
    only slot conflicts can be introduced, which `repair` then resolves.
    """
    n = len(parent_a)
    if n < 2:
        return [g.copy() for g in parent_a], [g.copy() for g in parent_b]

    p1, p2 = sorted(rng.sample(range(n), 2))
    child_a = [g.copy() for g in parent_a]
    child_b = [g.copy() for g in parent_b]

    for i in range(p1, p2):
        a_slot = (child_a[i].room_id, child_a[i].day, child_a[i].period)
        b_slot = (child_b[i].room_id, child_b[i].day, child_b[i].period)
        child_a[i].room_id, child_a[i].day, child_a[i].period = b_slot
        child_b[i].room_id, child_b[i].day, child_b[i].period = a_slot

    return child_a, child_b


# ---------------------------------------------------------------------------
# Mutation
# ---------------------------------------------------------------------------

def mutate(chromosome: Chromosome, ctx: ProblemContext, mutation_rate: float, rng: random.Random) -> None:
    """In-place mutation. Each gene independently mutates with probability
    `mutation_rate`, via one of: change day/period, change room, or swap
    slots with another random gene."""
    n = len(chromosome)
    for i in range(n):
        if rng.random() >= mutation_rate:
            continue
        move = rng.choice(("slot", "room", "swap"))
        if move == "slot":
            chromosome[i].day = rng.choice(ctx.dataset.days)
            chromosome[i].period = rng.randint(1, ctx.dataset.periods_per_day)
        elif move == "room":
            chromosome[i].room_id = rng.choice(ctx.dataset.rooms).room_id
        else:  # swap
            j = rng.randrange(n)
            if j == i:
                continue
            chromosome[i].day, chromosome[j].day = chromosome[j].day, chromosome[i].day
            chromosome[i].period, chromosome[j].period = chromosome[j].period, chromosome[i].period
            chromosome[i].room_id, chromosome[j].room_id = chromosome[j].room_id, chromosome[i].room_id


# ---------------------------------------------------------------------------
# Constraint repair
# ---------------------------------------------------------------------------

MAX_REPAIR_ATTEMPTS_PER_GENE = 8


def repair(chromosome: Chromosome, ctx: ProblemContext, rng: random.Random) -> None:
    """Bounded-attempt repair pass.

    For each hard-constraint dimension, find genes involved in a conflict and
    try to move them to a feasible slot (a slot where the faculty, batch, and
    room are all free, and the room has sufficient capacity). Each gene gets
    a fixed attempt budget so repair cannot loop forever; whatever remains
    unresolved is left for the fitness function to penalize.
    """
    occupancy_faculty = defaultdict(list)
    occupancy_batch = defaultdict(list)
    occupancy_room = defaultdict(list)
    for idx, g in enumerate(chromosome):
        occupancy_faculty[(g.faculty_id, g.day, g.period)].append(idx)
        occupancy_batch[(g.batch_id, g.day, g.period)].append(idx)
        occupancy_room[(g.room_id, g.day, g.period)].append(idx)

    conflicted_indices = set()
    for idx_list in list(occupancy_faculty.values()) + list(occupancy_batch.values()) + list(occupancy_room.values()):
        if len(idx_list) > 1:
            conflicted_indices.update(idx_list[1:])  # keep the first occupant, move the rest

    # also flag capacity violations
    for idx, g in enumerate(chromosome):
        room = ctx.room_by_id[g.room_id]
        batch = ctx.batch_by_id[g.batch_id]
        if room.capacity < batch.student_count:
            conflicted_indices.add(idx)

    days = ctx.dataset.days
    periods = list(range(1, ctx.dataset.periods_per_day + 1))
    suitable_rooms = defaultdict(list)  # batch_id -> rooms with enough capacity

    for idx in conflicted_indices:
        gene = chromosome[idx]
        batch = ctx.batch_by_id[gene.batch_id]
        if gene.batch_id not in suitable_rooms:
            suitable_rooms[gene.batch_id] = [r for r in ctx.dataset.rooms if r.capacity >= batch.student_count] or ctx.dataset.rooms

        for _ in range(MAX_REPAIR_ATTEMPTS_PER_GENE):
            day = rng.choice(days)
            period = rng.choice(periods)
            room = rng.choice(suitable_rooms[gene.batch_id])

            faculty_free = len(occupancy_faculty.get((gene.faculty_id, day, period), [])) == 0
            batch_free = len(occupancy_batch.get((gene.batch_id, day, period), [])) == 0
            room_free = len(occupancy_room.get((room.room_id, day, period), [])) == 0

            if faculty_free and batch_free and room_free:
                # remove old occupancy entries
                _discard(occupancy_faculty, (gene.faculty_id, gene.day, gene.period), idx)
                _discard(occupancy_batch, (gene.batch_id, gene.day, gene.period), idx)
                _discard(occupancy_room, (gene.room_id, gene.day, gene.period), idx)

                gene.day, gene.period, gene.room_id = day, period, room.room_id

                occupancy_faculty[(gene.faculty_id, day, period)].append(idx)
                occupancy_batch[(gene.batch_id, day, period)].append(idx)
                occupancy_room[(room.room_id, day, period)].append(idx)
                break
        # if no feasible slot found within the attempt budget, leave as-is;
        # the fitness function will penalize the remaining violation.


def _discard(occupancy: dict, key: tuple, idx: int) -> None:
    lst = occupancy.get(key)
    if lst and idx in lst:
        lst.remove(idx)

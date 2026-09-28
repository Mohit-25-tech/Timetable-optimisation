"""
Chromosome representation for the timetable Genetic Algorithm.

A GENE represents one scheduled class/session:
    (subject_id, faculty_id, batch_id, room_id, day, period)

A CHROMOSOME is a list of genes -- one gene per required session across the
whole university -- i.e. one complete candidate timetable.

A POPULATION is a list of chromosomes (candidate timetables).

The number of genes in every chromosome is fixed: it equals the total number
of sessions required (sum of `sessions_per_week` across all subjects). Only
the (room, day, period) part of each gene is subject to search; the
(subject, faculty, batch) part is fixed by the requirement the gene
represents, since that assignment is set by the curriculum, not chosen by
the optimizer.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List

from backend.models.schemas import DatasetInput


@dataclass
class Gene:
    subject_id: str
    faculty_id: str
    batch_id: str
    room_id: str
    day: str
    period: int

    def copy(self) -> "Gene":
        return Gene(self.subject_id, self.faculty_id, self.batch_id, self.room_id, self.day, self.period)


@dataclass
class RequiredSession:
    """One required (subject, occurrence) slot that must be scheduled somewhere."""
    subject_id: str
    faculty_id: str
    batch_id: str


@dataclass
class ProblemContext:
    """Precomputed lookups shared by every GA stage. Built once per optimize call."""
    dataset: DatasetInput
    required_sessions: List[RequiredSession]
    room_by_id: dict
    subject_by_id: dict
    batch_by_id: dict
    faculty_by_id: dict

    @staticmethod
    def build(dataset: DatasetInput) -> "ProblemContext":
        required: List[RequiredSession] = []
        for subj in dataset.subjects:
            for _ in range(subj.sessions_per_week):
                required.append(RequiredSession(subj.subject_id, subj.faculty_id, subj.batch_id))
        return ProblemContext(
            dataset=dataset,
            required_sessions=required,
            room_by_id={r.room_id: r for r in dataset.rooms},
            subject_by_id={s.subject_id: s for s in dataset.subjects},
            batch_by_id={b.batch_id: b for b in dataset.batches},
            faculty_by_id={f.faculty_id: f for f in dataset.faculty},
        )


Chromosome = List[Gene]


def random_slot(ctx: ProblemContext, rng: random.Random):
    """Pick a random (room, day, period) slot."""
    room = rng.choice(ctx.dataset.rooms)
    day = rng.choice(ctx.dataset.days)
    period = rng.randint(1, ctx.dataset.periods_per_day)
    return room.room_id, day, period


def create_random_chromosome(ctx: ProblemContext, rng: random.Random) -> Chromosome:
    """Build one random (likely infeasible) candidate timetable.

    Rooms are biased toward capacity/type fit where possible, which speeds up
    convergence without hand-coding the answer -- the GA still has to resolve
    day/period conflicts itself.
    """
    chromosome: Chromosome = []
    for req in ctx.required_sessions:
        subj = ctx.subject_by_id[req.subject_id]
        candidate_rooms = [
            r for r in ctx.dataset.rooms
            if r.capacity >= subj.expected_students
            and (subj.preferred_room_type is None or r.room_type == subj.preferred_room_type)
        ] or [r for r in ctx.dataset.rooms if r.capacity >= subj.expected_students] or ctx.dataset.rooms

        room = rng.choice(candidate_rooms)
        day = rng.choice(ctx.dataset.days)
        period = rng.randint(1, ctx.dataset.periods_per_day)
        chromosome.append(Gene(req.subject_id, req.faculty_id, req.batch_id, room.room_id, day, period))
    return chromosome


def create_greedy_chromosome(ctx: ProblemContext, rng: random.Random) -> Chromosome:
    """Build a chromosome using a greedy constructive heuristic.

    Strategy:
    - Sort required sessions by batch so that a batch's sessions are placed
      together, enabling consecutive-period placement that minimises idle gaps.
    - For each session, try candidate slots in a randomised order and pick the
      first slot that is conflict-free (faculty, batch, room all unoccupied) and
      where the room capacity is sufficient.  Prefer slots on the same day and
      adjacent to already-placed sessions for the same batch.
    - Falls back to a random slot if no conflict-free slot is found within the
      attempt budget.
    """
    from collections import defaultdict

    days = ctx.dataset.days
    periods = list(range(1, ctx.dataset.periods_per_day + 1))

    # Pre-sort sessions: group by batch, then by subject within batch.
    sorted_sessions = sorted(ctx.required_sessions, key=lambda r: (r.batch_id, r.subject_id))

    # Occupancy trackers (key -> True means occupied).
    occ_faculty: dict = {}   # (faculty_id, day, period) -> True
    occ_batch: dict = {}     # (batch_id, day, period) -> True
    occ_room: dict = {}      # (room_id, day, period) -> True

    # Track where each batch has already been placed, to prefer adjacent slots.
    batch_day_periods: dict = defaultdict(lambda: defaultdict(list))  # batch_id -> day -> [period]

    chromosome: Chromosome = []

    for req in sorted_sessions:
        subj = ctx.subject_by_id[req.subject_id]
        batch = ctx.batch_by_id[req.batch_id]

        # Candidate rooms: capacity-fit and type-fit, shuffled.
        candidate_rooms = [
            r for r in ctx.dataset.rooms
            if r.capacity >= batch.student_count
            and (subj.preferred_room_type is None or r.room_type == subj.preferred_room_type)
        ] or [r for r in ctx.dataset.rooms if r.capacity >= batch.student_count] or list(ctx.dataset.rooms)
        rng.shuffle(candidate_rooms)

        placed = False

        # Phase A: try to place adjacent to existing batch sessions (reduces gaps).
        existing_days = list(batch_day_periods[req.batch_id].keys())
        rng.shuffle(existing_days)
        for day in existing_days:
            existing_periods = batch_day_periods[req.batch_id][day]
            # Try periods adjacent to the existing span.
            adjacent = set()
            for p in existing_periods:
                if p - 1 >= 1:
                    adjacent.add(p - 1)
                if p + 1 <= ctx.dataset.periods_per_day:
                    adjacent.add(p + 1)
            adjacent -= set(existing_periods)
            adj_list = sorted(adjacent)
            rng.shuffle(adj_list)

            for period in adj_list:
                if occ_batch.get((req.batch_id, day, period)):
                    continue
                if occ_faculty.get((req.faculty_id, day, period)):
                    continue
                for room in candidate_rooms:
                    if not occ_room.get((room.room_id, day, period)):
                        # Place here.
                        chromosome.append(Gene(req.subject_id, req.faculty_id, req.batch_id,
                                               room.room_id, day, period))
                        occ_faculty[(req.faculty_id, day, period)] = True
                        occ_batch[(req.batch_id, day, period)] = True
                        occ_room[(room.room_id, day, period)] = True
                        batch_day_periods[req.batch_id][day].append(period)
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break

        if placed:
            continue

        # Phase B: try any free slot, randomised.
        day_list = list(days)
        rng.shuffle(day_list)
        for day in day_list:
            period_list = list(periods)
            rng.shuffle(period_list)
            for period in period_list:
                if occ_batch.get((req.batch_id, day, period)):
                    continue
                if occ_faculty.get((req.faculty_id, day, period)):
                    continue
                for room in candidate_rooms:
                    if not occ_room.get((room.room_id, day, period)):
                        chromosome.append(Gene(req.subject_id, req.faculty_id, req.batch_id,
                                               room.room_id, day, period))
                        occ_faculty[(req.faculty_id, day, period)] = True
                        occ_batch[(req.batch_id, day, period)] = True
                        occ_room[(room.room_id, day, period)] = True
                        batch_day_periods[req.batch_id][day].append(period)
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break

        if not placed:
            # Phase C: fallback to random slot (will likely have conflicts).
            room = rng.choice(candidate_rooms)
            day = rng.choice(days)
            period = rng.choice(periods)
            chromosome.append(Gene(req.subject_id, req.faculty_id, req.batch_id,
                                   room.room_id, day, period))
            occ_faculty[(req.faculty_id, day, period)] = True
            occ_batch[(req.batch_id, day, period)] = True
            occ_room[(room.room_id, day, period)] = True
            batch_day_periods[req.batch_id][day].append(period)

    return chromosome


def create_initial_population(ctx: ProblemContext, size: int, rng: random.Random,
                              greedy_fraction: float = 0.0) -> List[Chromosome]:
    """Create the initial population.

    Args:
        greedy_fraction: Fraction of individuals seeded with the greedy
            constructive heuristic (0.0 = all random, matching original behaviour).
    """
    population: List[Chromosome] = []
    greedy_count = int(size * greedy_fraction)
    for i in range(size):
        if i < greedy_count:
            population.append(create_greedy_chromosome(ctx, rng))
        else:
            population.append(create_random_chromosome(ctx, rng))
    return population

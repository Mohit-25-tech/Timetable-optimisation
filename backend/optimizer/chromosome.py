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


def create_initial_population(ctx: ProblemContext, size: int, rng: random.Random) -> List[Chromosome]:
    return [create_random_chromosome(ctx, rng) for _ in range(size)]

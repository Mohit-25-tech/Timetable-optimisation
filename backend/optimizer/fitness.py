"""
Cost / fitness function and constraint detection.

Lower cost = better solution.
Higher fitness = better solution.
fitness = 1 / (1 + total_cost)

Hard constraints (must ideally become zero):
  - Faculty conflict: a faculty member teaching two classes at once
  - Room conflict: a room hosting two classes at once
  - Student/batch conflict: a batch attending two classes at once
  - Capacity violation: room capacity < batch size

Soft constraints (should be minimized):
  - Faculty idle gaps between classes on a day
  - Student/batch idle gaps between classes on a day
  - Uneven distribution of a subject's sessions across the week
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Tuple

from backend.models.schemas import GAConfig
from backend.optimizer.chromosome import Chromosome, ProblemContext


@dataclass
class ConstraintCounts:
    faculty_conflicts: int = 0
    student_conflicts: int = 0
    room_conflicts: int = 0
    capacity_violations: int = 0
    faculty_gaps: int = 0
    student_gaps: int = 0
    distribution_penalty_units: int = 0

    @property
    def hard_total(self) -> int:
        return self.faculty_conflicts + self.student_conflicts + self.room_conflicts + self.capacity_violations


def _count_conflicts(chromosome: Chromosome, key_fn) -> int:
    """Count pairwise conflicts for entities that share a (day, period, key) slot."""
    slots: Dict[Tuple, int] = defaultdict(int)
    for gene in chromosome:
        slots[(key_fn(gene), gene.day, gene.period)] += 1
    conflicts = 0
    for count in slots.values():
        if count > 1:
            conflicts += count - 1  # each extra class beyond the first is one conflict
    return conflicts


def _capacity_violations(chromosome: Chromosome, ctx: ProblemContext) -> int:
    violations = 0
    for gene in chromosome:
        room = ctx.room_by_id[gene.room_id]
        batch = ctx.batch_by_id[gene.batch_id]
        if room.capacity < batch.student_count:
            violations += 1
    return violations


def _gaps_for_entity(chromosome: Chromosome, entity_key_fn, ctx: ProblemContext) -> int:
    """Sum of idle-period gaps between an entity's first and last class each day."""
    by_entity_day: Dict[Tuple, List[int]] = defaultdict(list)
    for gene in chromosome:
        by_entity_day[(entity_key_fn(gene), gene.day)].append(gene.period)

    total_gaps = 0
    for periods in by_entity_day.values():
        periods = sorted(set(periods))
        if len(periods) < 2:
            continue
        span = periods[-1] - periods[0] + 1
        occupied = len(periods)
        total_gaps += max(0, span - occupied)
    return total_gaps


def _distribution_penalty(chromosome: Chromosome) -> int:
    """Penalize a subject's weekly sessions being clustered on the same day
    instead of spread out (e.g. all 3 sessions crammed into one day)."""
    by_subject_day: Dict[Tuple, int] = defaultdict(int)
    for gene in chromosome:
        by_subject_day[(gene.subject_id, gene.day)] += 1
    penalty = 0
    for count in by_subject_day.values():
        if count > 1:
            penalty += count - 1
    return penalty


def evaluate(chromosome: Chromosome, ctx: ProblemContext, config: GAConfig) -> Tuple[float, float, ConstraintCounts]:
    """Return (total_cost, fitness, constraint_counts) for a chromosome."""
    counts = ConstraintCounts(
        faculty_conflicts=_count_conflicts(chromosome, lambda g: ("faculty", g.faculty_id)),
        student_conflicts=_count_conflicts(chromosome, lambda g: ("batch", g.batch_id)),
        room_conflicts=_count_conflicts(chromosome, lambda g: ("room", g.room_id)),
        capacity_violations=_capacity_violations(chromosome, ctx),
        faculty_gaps=_gaps_for_entity(chromosome, lambda g: ("faculty", g.faculty_id), ctx),
        student_gaps=_gaps_for_entity(chromosome, lambda g: ("batch", g.batch_id), ctx),
        distribution_penalty_units=_distribution_penalty(chromosome),
    )

    total_cost = (
        config.hard_faculty_conflict * counts.faculty_conflicts
        + config.hard_student_conflict * counts.student_conflicts
        + config.hard_room_conflict * counts.room_conflicts
        + config.capacity_violation * counts.capacity_violations
        + config.faculty_gap * counts.faculty_gaps
        + config.student_gap * counts.student_gaps
        + config.distribution_penalty * counts.distribution_penalty_units
    )

    fitness = 1.0 / (1.0 + total_cost)
    return total_cost, fitness, counts


def soft_cost_only(counts: ConstraintCounts, config: GAConfig) -> float:
    return (
        config.faculty_gap * counts.faculty_gaps
        + config.student_gap * counts.student_gaps
        + config.distribution_penalty * counts.distribution_penalty_units
    )

"""Pydantic models for request/response validation."""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class Subject(BaseModel):
    subject_id: str
    name: str
    faculty_id: str
    batch_id: str
    sessions_per_week: int = Field(gt=0, le=10)
    expected_students: int = Field(gt=0)
    preferred_room_type: Optional[str] = None


class Faculty(BaseModel):
    faculty_id: str
    name: str
    department: str


class Room(BaseModel):
    room_id: str
    room_number: str
    capacity: int = Field(gt=0)
    room_type: str = "Lecture"


class Batch(BaseModel):
    batch_id: str
    name: str
    student_count: int = Field(gt=0)


class DatasetInput(BaseModel):
    subjects: List[Subject]
    faculty: List[Faculty]
    rooms: List[Room]
    batches: List[Batch]
    days: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    periods_per_day: int = Field(default=6, gt=0, le=12)


class GAConfig(BaseModel):
    population_size: int = Field(default=100, ge=10, le=1000)
    generations: int = Field(default=200, ge=1, le=5000)
    mutation_rate: float = Field(default=0.10, ge=0.0, le=1.0)
    crossover_rate: float = Field(default=0.80, ge=0.0, le=1.0)
    tournament_size: int = Field(default=3, ge=2, le=20)
    elite_count: int = Field(default=5, ge=0, le=50)
    stagnation_limit: Optional[int] = Field(default=40, ge=1)
    random_seed: Optional[int] = None

    hard_faculty_conflict: float = 1000.0
    hard_student_conflict: float = 1000.0
    hard_room_conflict: float = 1000.0
    capacity_violation: float = 500.0
    faculty_gap: float = 10.0
    student_gap: float = 10.0
    distribution_penalty: float = 5.0


class OptimizeRequest(BaseModel):
    dataset: DatasetInput
    config: GAConfig = GAConfig()


class GeneOut(BaseModel):
    subject_id: str
    subject_name: str
    faculty_id: str
    faculty_name: str
    batch_id: str
    batch_name: str
    room_id: str
    room_number: str
    day: str
    period: int


class GenerationStat(BaseModel):
    generation: int
    best_fitness: float
    avg_fitness: float
    best_cost: float
    hard_violations: int
    soft_penalty: float


class ConstraintReport(BaseModel):
    faculty_conflicts: int
    student_conflicts: int
    room_conflicts: int
    capacity_violations: int
    faculty_gaps: int
    student_gaps: int
    distribution_penalties: int = 0


class InitialMetrics(BaseModel):
    hard_violations: int
    soft_violations: int
    faculty_conflicts: int
    student_conflicts: int
    room_conflicts: int
    capacity_violations: int
    faculty_gaps: int
    student_gaps: int
    distribution_penalties: int = 0
    total_cost: float
    fitness: float


class OptimizeResponse(BaseModel):
    timetable: List[GeneOut]
    history: List[GenerationStat]
    final_cost: float
    final_fitness: float
    constraints: ConstraintReport
    generations_executed: int
    execution_time_seconds: float
    population_size: int
    converged_early: bool
    initial_metrics: Optional[InitialMetrics] = None

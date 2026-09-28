"""
FastAPI backend for the University Timetable Optimizer.

Endpoints:
    GET  /api/demo-data   -> a ready-to-use sample dataset
    POST /api/optimize    -> run the real Genetic Algorithm and return the
                             optimized timetable, convergence history, and
                             constraint report
    POST /api/export/csv  -> export a given timetable as CSV
    GET  /api/health      -> health check
"""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List

from backend.models.schemas import (
    OptimizeRequest, OptimizeResponse, GeneOut, GenerationStat, ConstraintReport, DatasetInput,
    InitialMetrics,
)
from backend.data.sample_data import build_sample_dataset
from backend.optimizer.ga import run_ga
from backend.utils.export import timetable_to_csv

app = FastAPI(title="University Timetable Optimizer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/demo-data", response_model=DatasetInput)
def demo_data():
    return build_sample_dataset()


@app.post("/api/optimize", response_model=OptimizeResponse)
def optimize(request: OptimizeRequest):
    dataset = request.dataset
    if not dataset.subjects:
        raise HTTPException(status_code=422, detail="Dataset must include at least one subject.")

    try:
        result = run_ga(dataset, request.config)
    except Exception as exc:  # pragma: no cover - defensive; GA itself is deterministic given valid input
        raise HTTPException(status_code=500, detail=f"Optimization failed: {exc}") from exc

    ctx = result.context
    timetable: List[GeneOut] = []
    for gene in result.best_chromosome:
        subj = ctx.subject_by_id[gene.subject_id]
        fac = ctx.faculty_by_id[gene.faculty_id]
        batch = ctx.batch_by_id[gene.batch_id]
        room = ctx.room_by_id[gene.room_id]
        timetable.append(GeneOut(
            subject_id=gene.subject_id, subject_name=subj.name,
            faculty_id=gene.faculty_id, faculty_name=fac.name,
            batch_id=gene.batch_id, batch_name=batch.name,
            room_id=gene.room_id, room_number=room.room_number,
            day=gene.day, period=gene.period,
        ))

    history = [
        GenerationStat(
            generation=h.generation, best_fitness=h.best_fitness, avg_fitness=h.avg_fitness,
            best_cost=h.best_cost, hard_violations=h.hard_violations, soft_penalty=h.soft_penalty,
        )
        for h in result.history
    ]

    constraints = ConstraintReport(
        faculty_conflicts=result.best_counts.faculty_conflicts,
        student_conflicts=result.best_counts.student_conflicts,
        room_conflicts=result.best_counts.room_conflicts,
        capacity_violations=result.best_counts.capacity_violations,
        faculty_gaps=result.best_counts.faculty_gaps,
        student_gaps=result.best_counts.student_gaps,
        distribution_penalties=result.best_counts.distribution_penalty_units,
    )

    initial_metrics = None
    if result.initial_counts is not None:
        initial_soft = (
            result.initial_counts.faculty_gaps
            + result.initial_counts.student_gaps
            + result.initial_counts.distribution_penalty_units
        )
        initial_metrics = InitialMetrics(
            hard_violations=result.initial_counts.hard_total,
            soft_violations=initial_soft,
            faculty_conflicts=result.initial_counts.faculty_conflicts,
            student_conflicts=result.initial_counts.student_conflicts,
            room_conflicts=result.initial_counts.room_conflicts,
            capacity_violations=result.initial_counts.capacity_violations,
            faculty_gaps=result.initial_counts.faculty_gaps,
            student_gaps=result.initial_counts.student_gaps,
            distribution_penalties=result.initial_counts.distribution_penalty_units,
            total_cost=result.initial_cost,
            fitness=result.initial_fitness,
        )

    return OptimizeResponse(
        timetable=timetable,
        history=history,
        final_cost=result.best_cost,
        final_fitness=result.best_fitness,
        constraints=constraints,
        generations_executed=result.generations_executed,
        execution_time_seconds=result.execution_time_seconds,
        population_size=request.config.population_size,
        converged_early=result.converged_early,
        initial_metrics=initial_metrics,
    )


class ExportRequest(BaseModel):
    timetable: List[GeneOut]


@app.post("/api/export/csv", response_class=PlainTextResponse)
def export_csv(request: ExportRequest):
    return timetable_to_csv(request.timetable)

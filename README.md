# University Timetable Optimizer

A Constraint-Aware Genetic Algorithm, implemented from scratch in Python, that
generates a university timetable and demonstrably resolves faculty, room, and
batch conflicts across a real academic dataset — with a FastAPI backend and a
React/TypeScript dashboard for running it, watching it converge, and
inspecting the result.

This is an academic prototype. The optimization algorithm is the core
deliverable; the UI exists to make that algorithm easy to run and explain.

---

## 1. Project Overview

University timetabling assigns every required class session — a
(subject, faculty, batch) triple that must occur `sessions_per_week` times —
to a (room, day, period) slot. The assignment must respect hard constraints
(no faculty/room/batch double-booking, sufficient room capacity) while
minimizing soft-constraint costs (idle gaps, uneven distribution across the
week).

This is a **discrete combinatorial optimization problem** with a very large
search space and a non-differentiable objective, so gradient-based methods
don't apply. This project uses a **Constraint-Aware Genetic Algorithm**
instead: it evolves a population of candidate timetables generation by
generation toward a high-quality *feasible* solution. It does not claim to
guarantee the mathematical global optimum — only a strong, explainable one.

## 2. Features

- Real, from-scratch Genetic Algorithm (no black-box timetabling library)
- Realistic sample dataset (30 subjects, 20 faculty, 10 rooms, 5 batches, 5
  days × 6 periods) so the app works immediately with no manual data entry
- Configurable GA parameters from the UI (population size, generations,
  mutation/crossover rate, tournament size, elite count, stagnation limit,
  random seed)
- Live fitness/cost convergence chart, generation by generation
- Hard vs. soft constraint violation report
- Filterable timetable (by day, batch, faculty, room)
- CSV export
- An in-app "Algorithm Explainer" panel to walk a professor through every GA
  stage during a viva
- Backend test suite (pytest) covering constraint detection, fitness, every
  genetic operator, full GA execution, and the API
- An explanatory Jupyter notebook that imports the *same* optimizer code as
  the backend — there is only one GA implementation in this project

## 3. The Genetic Algorithm

```
Input Data
    ↓
Chromosome Representation
    ↓
Initial Population
    ↓
Fitness Evaluation
    ↓
Tournament Selection
    ↓
Crossover
    ↓
Mutation
    ↓
Constraint Repair
    ↓
Elitism
    ↓
Next Generation
    ↓
Termination
    ↓
Best Timetable
```

### Chromosome

A **gene** is one scheduled session:

```python
{
    "subject_id": "...",
    "faculty_id": "...",
    "batch_id": "...",
    "room_id": "...",
    "day": "...",
    "period": ...
}
```

A **chromosome** is the full ordered list of genes — one gene per required
session across the entire curriculum — i.e. one complete candidate timetable.
A **population** is a list of chromosomes evaluated in parallel each
generation. Because the (subject, faculty, batch) identity of every gene is
fixed by the curriculum requirement it represents, the GA only searches over
each gene's (room, day, period) — the part that's actually a scheduling
decision.

### Fitness

```
Total Cost =
    W1 × Faculty Conflicts
  + W2 × Student Conflicts
  + W3 × Room Conflicts
  + W4 × Capacity Violations
  + W5 × Faculty Gaps
  + W6 × Student Gaps
  + W7 × Distribution Penalties

fitness = 1 / (1 + total_cost)
```

Hard-constraint weights (1000 / 500) dominate soft-constraint weights (5–10)
by construction, so the GA always prefers a feasible-but-imperfect schedule
over an infeasible one. Lower cost = better solution; higher fitness = better
solution. Weights are configurable in `backend/models/schemas.py`
(`GAConfig`).

### Selection — Tournament Selection

```
Randomly select K candidates
        ↓
Compare fitness
        ↓
Select best candidate as parent
```

Tournament size `K` is configurable from the UI.

### Crossover — Two-Point Crossover

A timetable-appropriate crossover: two cut points are chosen over the flat
gene list, and the (room, day, period) segment between them is swapped
between two parents. Gene identity (subject/faculty/batch) never changes, so
every required session is always present after crossover — but crossover
**can** introduce faculty/room/batch conflicts, which is exactly why the
repair stage exists.

### Mutation

Each gene independently mutates with probability `mutation_rate`, via one of:
1. Change its day/period
2. Change its room
3. Swap slots with another random gene

This maintains population diversity and helps the GA avoid premature
convergence on a mediocre solution.

### Constraint Repair

A bounded-attempt local search run after crossover/mutation: for each gene
involved in a conflict, try up to 8 random feasible slots (faculty, batch,
and room all free, room capacity sufficient) and move the gene there. The
attempt count is capped so repair can never loop forever — anything left
unresolved is simply penalized by the fitness function on the next
evaluation.

### Elitism

The best `elite_count` individuals are copied unchanged into the next
generation, so the best solution found so far can never be lost to
crossover or mutation.

### Termination

Configurable via `generations` (hard cap) and `stagnation_limit` (early stop
once zero hard violations are reached and the best cost hasn't improved for
that many generations).

**Default configuration:**

```
Population size = 100
Generations = 200
Mutation rate = 0.10
Crossover rate = 0.80
Tournament size = 3
Elite count = 5
```

## 4. Constraints

**Hard constraints** (must ideally become zero):
- Faculty conflict — a faculty member cannot teach two classes at once
- Room conflict — a room cannot host two classes at once
- Student/batch conflict — a batch cannot attend two classes at once
- Room capacity — capacity must be ≥ the batch's student count
- Valid assignment — every required session must be scheduled (guaranteed by
  the chromosome representation itself)

**Soft constraints** (minimized, not required to reach zero):
- Faculty idle-period gaps within a day
- Student/batch idle-period gaps within a day
- Uneven distribution of a subject's sessions across the week

## 5. Architecture

```
React Frontend (TypeScript, Vite)
      ↓  fetch()
FastAPI (Python)
      ↓
Genetic Algorithm (backend/optimizer/)
      ↓
Optimized Timetable + Convergence History + Constraint Report
```

```
university-timetable-optimizer/
│
├── backend/
│   ├── main.py                 FastAPI app & endpoints
│   ├── requirements.txt
│   ├── models/schemas.py       Pydantic request/response models
│   ├── optimizer/
│   │   ├── chromosome.py       Gene/Chromosome representation, population init
│   │   ├── fitness.py          Cost function, constraint detection
│   │   ├── operators.py        Selection, crossover, mutation, repair
│   │   └── ga.py                Full GA loop
│   ├── data/sample_data.py     Sample dataset generator
│   └── utils/export.py         CSV export
│
├── frontend/
│   ├── package.json, vite.config.ts, tsconfig.json
│   └── src/
│       ├── App.tsx, api.ts, types.ts
│       └── components/          ConfigPanel, FitnessChart, ConstraintPanel,
│                                 TimetableView, AlgorithmExplainer
│
├── notebooks/
│   └── genetic_algorithm_explanation.ipynb   imports backend/optimizer directly
│
├── tests/
│   ├── test_constraints.py
│   ├── test_fitness.py
│   └── test_genetic_algorithm.py
│
├── README.md
├── .gitignore
└── LICENSE
```

## 6. Installation

Requires Python 3.10+ and Node.js 18+.

**Backend** (run these from the project root, `university-timetable-optimizer/`):

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

**Frontend:**

```bash
cd frontend
npm install
```

## 7. Running the Application

The backend package uses absolute imports (`backend.models...`), so it must
be started **from the project root**, not from inside `backend/`:

```bash
# from the project root, with venv activated
uvicorn backend.main:app --reload
```

This starts the API at `http://localhost:8000`.

In a second terminal:

```bash
cd frontend
npm run dev
```

This starts the UI at `http://localhost:5173`. Open it in a browser — it
loads the sample dataset automatically, and the "Run Optimization" button
triggers the GA via the backend.

If the backend isn't running, the UI shows: *"Backend unavailable. Please
start the FastAPI server."*

## 8. API Documentation

FastAPI serves interactive docs at `http://localhost:8000/docs` once running.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/demo-data` | Returns the sample dataset (`DatasetInput`) |
| `POST` | `/api/optimize` | Body: `{ dataset, config }` → runs the GA, returns the timetable, generation-by-generation history, final cost/fitness, and constraint report |
| `POST` | `/api/export/csv` | Body: `{ timetable }` → returns the timetable as CSV text |

## 9. Testing

```bash
# from the project root, with venv activated
pytest tests/ -v
```

16 tests cover: hard-constraint detection (faculty/room/batch/capacity),
the fitness/cost function, chromosome initialization, crossover, mutation,
repair, tournament selection, full GA execution (including reaching zero
hard violations on the demo dataset), and the `/api/optimize` endpoint.

## 10. Viva Questions

**Why Genetic Algorithm?**
Timetabling is a discrete combinatorial problem with a huge search space and
a non-differentiable objective — a GA searches that space efficiently for a
strong feasible solution without needing gradients.

**What is a chromosome?**
One complete candidate timetable: an ordered list of genes, one per required
class session.

**What is a gene?**
One scheduled session — subject, faculty, batch, room, day, and period.

**What is the fitness function?**
`1 / (1 + total_cost)`, where `total_cost` is a weighted sum of hard- and
soft-constraint violations. Lower cost → higher fitness.

**Why are hard constraints given higher penalties?**
So the GA always prefers a feasible-but-imperfect schedule (only soft
violations) over an infeasible one, no matter how good the infeasible
schedule's soft metrics look.

**Why use tournament selection?**
It's simple, tunable via tournament size, and naturally applies more
selection pressure toward fitter individuals without requiring the whole
population to be sorted.

**What does crossover do?**
Swaps a segment of (room, day, period) assignments between two parent
timetables, combining traits from both.

**Why is mutation necessary?**
It introduces novel variation the current population doesn't have, which
prevents premature convergence on a local optimum.

**Why is elitism used?**
To guarantee the best solution found so far survives into the next
generation, even if crossover and mutation only produce worse offspring that
round.

**What is constraint repair?**
A bounded-attempt process that, after crossover/mutation, tries to move a
conflicting gene to a feasible (room, day, period) slot.

**Why not gradient descent?**
The decision variables (room/day/period assignments) are discrete, and the
constraint-violation-based objective is not differentiable.

**Does GA guarantee the global optimum?**
No. It's a heuristic search that reliably finds high-quality feasible
solutions, not a proof of optimality.

**What happens if crossover creates conflicts?**
The repair stage runs immediately afterward and attempts to resolve them;
anything it can't fix is penalized by the fitness function.

**What happens if the algorithm gets stuck?**
The `stagnation_limit` parameter triggers early termination once the best
cost hasn't improved for that many generations and zero hard violations have
already been reached.

**How does the algorithm know a timetable is good?**
Its fitness score — computed from the same weighted cost function every
candidate is evaluated against, so "good" is defined consistently across the
whole population and every generation.

import type { DatasetInput, GAConfig, OptimizeResponse } from "../types";

interface Props {
  result: OptimizeResponse;
  config: GAConfig;
  dataset: DatasetInput;
}

export default function RunSummary({ result, config, dataset }: Props) {
  const c = result.constraints;
  const hardTotal = c.faculty_conflicts + c.student_conflicts + c.room_conflicts + c.capacity_violations;
  const softTotal = c.faculty_gaps + c.student_gaps + (c.distribution_penalties ?? 0);
  const totalSessions = dataset.subjects.reduce((sum, s) => sum + s.sessions_per_week, 0);

  return (
    <div className="card run-summary-card">
      <div className="card-header-row">
        <h2>Run Summary</h2>
        <span className={`status-pill ${hardTotal === 0 ? "ok" : "down"}`}>
          {hardTotal === 0 ? "✓ Feasible Timetable Found" : "⚠ Infeasible Timetable"}
        </span>
      </div>

      <div className="summary-columns-grid">
        {/* Column 1: Dataset */}
        <div className="summary-col">
          <div className="col-title">Dataset Specification</div>
          <div className="summary-list">
            <div className="summary-item">
              <span className="s-label">Scope:</span>
              <span className="s-value">
                {dataset.subjects.length} subjects · {dataset.faculty.length} faculty · {dataset.rooms.length} rooms · {dataset.batches.length} batches
              </span>
            </div>
            <div className="summary-item">
              <span className="s-label">Total Required:</span>
              <span className="s-value">{totalSessions} sessions / week</span>
            </div>
            <div className="summary-item">
              <span className="s-label">Available Slots:</span>
              <span className="s-value">
                {dataset.days.length * dataset.periods_per_day * dataset.rooms.length} room-period slots ({dataset.days.length} days × {dataset.periods_per_day} periods × {dataset.rooms.length} rooms)
              </span>
            </div>
          </div>
        </div>

        {/* Column 2: GA Configuration */}
        <div className="summary-col">
          <div className="col-title">GA Configuration</div>
          <div className="summary-list">
            <div className="summary-item">
              <span className="s-label">Population:</span>
              <span className="s-value">{config.population_size}</span>
            </div>
            <div className="summary-item">
              <span className="s-label">Generations Cap:</span>
              <span className="s-value">{config.generations}</span>
            </div>
            <div className="summary-item">
              <span className="s-label">Operators:</span>
              <span className="s-value">
                Mut: {config.mutation_rate.toFixed(2)} · Cross: {config.crossover_rate.toFixed(2)}
              </span>
            </div>
            <div className="summary-item">
              <span className="s-label">Selection / Elitism:</span>
              <span className="s-value">
                Tournament: {config.tournament_size} · Elites: {config.elite_count}
              </span>
            </div>
            <div className="summary-item">
              <span className="s-label">Stagnation Limit:</span>
              <span className="s-value">{config.stagnation_limit ?? "None"}</span>
            </div>
          </div>
        </div>

        {/* Column 3: Result */}
        <div className="summary-col">
          <div className="col-title">Execution Result</div>
          <div className="summary-list">
            <div className="summary-item">
              <span className="s-label">Hard Violations:</span>
              <span className={`s-value ${hardTotal === 0 ? "text-success" : "text-danger"}`}>
                {hardTotal}
              </span>
            </div>
            <div className="summary-item">
              <span className="s-label">Soft Violations:</span>
              <span className="s-value">{softTotal}</span>
            </div>
            <div className="summary-item">
              <span className="s-label">Final Cost:</span>
              <span className="s-value">{result.final_cost.toLocaleString(undefined, { maximumFractionDigits: 1 })}</span>
            </div>
            <div className="summary-item">
              <span className="s-label">Final Fitness:</span>
              <span className="s-value">{result.final_fitness.toFixed(6)}</span>
            </div>
            <div className="summary-item">
              <span className="s-label">Generations Run:</span>
              <span className="s-value">
                {result.generations_executed} {result.converged_early ? "(early stop plateau)" : ""}
              </span>
            </div>
            <div className="summary-item">
              <span className="s-label">Execution Time:</span>
              <span className="s-value">{result.execution_time_seconds.toFixed(2)}s</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

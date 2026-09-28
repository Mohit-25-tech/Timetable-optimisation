import type { OptimizeResponse } from "../types";

interface Props {
  result: OptimizeResponse;
}

export default function OptimizationResult({ result }: Props) {
  const c = result.constraints;
  const hardTotal = c.faculty_conflicts + c.student_conflicts + c.room_conflicts + c.capacity_violations;
  const softTotal = c.faculty_gaps + c.student_gaps + (c.distribution_penalties ?? 0);
  const isFeasible = hardTotal === 0;

  // Extract initial metrics from initial_metrics or fallback to history[0]
  const initial = result.initial_metrics ?? (result.history.length > 0 ? {
    hard_violations: result.history[0].hard_violations,
    soft_violations: Math.round(result.history[0].soft_penalty / 10), // approximate if raw counts missing
    faculty_conflicts: 0,
    student_conflicts: 0,
    room_conflicts: 0,
    capacity_violations: 0,
    faculty_gaps: 0,
    student_gaps: 0,
    distribution_penalties: 0,
    total_cost: result.history[0].best_cost,
    fitness: result.history[0].best_fitness,
  } : null);

  // Compute mathematically sound improvements
  const costReductionPct = initial && initial.total_cost > 0
    ? (((initial.total_cost - result.final_cost) / initial.total_cost) * 100)
    : null;

  const fitnessIncreasePct = initial && initial.fitness > 0
    ? (((result.final_fitness - initial.fitness) / initial.fitness) * 100)
    : null;

  const softReductionPct = initial && initial.soft_violations > 0
    ? (((initial.soft_violations - softTotal) / initial.soft_violations) * 100)
    : null;

  return (
    <div className="card optimization-result-card">
      <div className={`result-status-banner ${isFeasible ? "feasible" : "infeasible"}`}>
        <div className="status-main">
          <div className="status-badge-icon">{isFeasible ? "✓" : "⚠"}</div>
          <div>
            <div className="status-title">
              {isFeasible ? "Feasible Timetable ✓" : "Infeasible Timetable"}
            </div>
            <div className="status-subtitle">
              {isFeasible
                ? "All hard constraints satisfied · Best feasible timetable found by the Genetic Algorithm"
                : `Hard constraint violations remain (${hardTotal} unresolved)`}
            </div>
          </div>
        </div>
        {result.converged_early && (
          <span className="early-stop-pill">Early Convergence Reached</span>
        )}
      </div>

      <div className="stat-row key-metrics-row">
        <div className={`stat ${isFeasible ? "good" : "bad"}`}>
          <div className="value">{hardTotal}</div>
          <div className="label">Hard Violations</div>
        </div>
        <div className="stat warning-stat">
          <div className="value">{softTotal}</div>
          <div className="label">Soft Violations</div>
        </div>
        <div className="stat">
          <div className="value">{result.final_cost.toLocaleString(undefined, { maximumFractionDigits: 1 })}</div>
          <div className="label">Final Cost</div>
        </div>
        <div className="stat">
          <div className="value">{result.final_fitness.toFixed(6)}</div>
          <div className="label">Final Fitness</div>
        </div>
        <div className="stat">
          <div className="value">{result.generations_executed}</div>
          <div className="label">Generations Executed</div>
        </div>
        <div className="stat">
          <div className="value">{result.execution_time_seconds.toFixed(2)}s</div>
          <div className="label">Execution Time</div>
        </div>
      </div>

      {initial && (
        <div className="improvement-section">
          <h3>Optimization Improvement (Before vs. After)</h3>
          <p className="section-subtext">
            Actual quantitative progression from the best candidate of the randomly initialized population (Gen 1)
            to the final evolved timetable.
          </p>
          <div className="comparison-table-wrapper">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Direction</th>
                  <th>Initial (Gen 1)</th>
                  <th>Final (Gen {result.generations_executed})</th>
                  <th>Improvement</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Hard Violations</strong></td>
                  <td><span className="direction-badge lower">Lower is better</span></td>
                  <td>{initial.hard_violations}</td>
                  <td className={isFeasible ? "highlight-success" : "highlight-danger"}>
                    {hardTotal}
                  </td>
                  <td>
                    {initial.hard_violations > 0 && hardTotal === 0 ? (
                      <span className="diff-tag success">100% eliminated (-{initial.hard_violations})</span>
                    ) : initial.hard_violations > hardTotal ? (
                      <span className="diff-tag success">
                        -{initial.hard_violations - hardTotal} violations
                      </span>
                    ) : (
                      <span className="diff-tag neutral">No change</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td><strong>Total Cost</strong></td>
                  <td><span className="direction-badge lower">Lower is better</span></td>
                  <td>{initial.total_cost.toLocaleString(undefined, { maximumFractionDigits: 1 })}</td>
                  <td className="highlight-success">
                    {result.final_cost.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                  </td>
                  <td>
                    {costReductionPct !== null && costReductionPct >= 0 ? (
                      <span className="diff-tag success">
                        -{costReductionPct.toFixed(1)}% reduction
                      </span>
                    ) : (
                      <span className="diff-tag neutral">—</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td><strong>Fitness Score</strong></td>
                  <td><span className="direction-badge higher">Higher is better</span></td>
                  <td>{initial.fitness.toFixed(6)}</td>
                  <td className="highlight-success">{result.final_fitness.toFixed(6)}</td>
                  <td>
                    {fitnessIncreasePct !== null && fitnessIncreasePct >= 0 ? (
                      <span className="diff-tag success">
                        +{fitnessIncreasePct.toLocaleString(undefined, { maximumFractionDigits: 0 })}% increase
                      </span>
                    ) : (
                      <span className="diff-tag neutral">—</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td><strong>Soft Violations</strong></td>
                  <td><span className="direction-badge lower">Lower is better</span></td>
                  <td>{initial.soft_violations}</td>
                  <td className="highlight-neutral">{softTotal}</td>
                  <td>
                    {softReductionPct !== null && softReductionPct > 0 ? (
                      <span className="diff-tag success">
                        -{softReductionPct.toFixed(1)}% reduction (-{initial.soft_violations - softTotal})
                      </span>
                    ) : initial.soft_violations === softTotal ? (
                      <span className="diff-tag neutral">Balanced with hard constraints</span>
                    ) : (
                      <span className="diff-tag neutral">
                        +{softTotal - initial.soft_violations} (trade-off)
                      </span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="improvement-note">
            <em>* Note:</em> Initial values represent the best candidate solution evaluated in Generation 1 from the
            randomly initialized population before genetic operations (selection, crossover, mutation, and repair) were iteratively applied.
          </div>
        </div>
      )}
    </div>
  );
}

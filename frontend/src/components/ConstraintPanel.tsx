import type { ConstraintReport, OptimizeResponse } from "../types";

interface Props {
  result: OptimizeResponse;
}

export default function ConstraintPanel({ result }: Props) {
  const c: ConstraintReport = result.constraints;
  const hardTotal = c.faculty_conflicts + c.student_conflicts + c.room_conflicts + c.capacity_violations;
  const distributionPenalties = c.distribution_penalties ?? 0;
  const softTotal = c.faculty_gaps + c.student_gaps + distributionPenalties;

  return (
    <div className="card constraint-card">
      <div className="card-header-row">
        <h2>Constraint Analysis &amp; Verification</h2>
        <span className={`status-pill ${hardTotal === 0 ? "ok" : "down"}`}>
          {hardTotal === 0 ? "0 Hard Violations (Feasible)" : `${hardTotal} Hard Violations Remaining`}
        </span>
      </div>

      <p className="constraint-intro-text">
        <strong>Constraint Definition:</strong> Hard constraints must be satisfied for a feasible timetable.
        Soft constraints are optimization preferences and contribute to the objective cost.
      </p>

      <div className="constraint-sections-grid">
        {/* HARD CONSTRAINTS */}
        <div className="constraint-block hard-block">
          <div className="constraint-block-header">
            <h3>Hard Constraints (Feasibility Requirements)</h3>
            <span className={`constraint-status-tag ${hardTotal === 0 ? "pass" : "fail"}`}>
              {hardTotal === 0 ? "All Satisfied ✓" : "Violations Detected"}
            </span>
          </div>
          <ul className="constraint-items">
            <li className="constraint-item">
              <div className="constraint-desc">
                <span className="check-icon">{c.faculty_conflicts === 0 ? "✓" : "✗"}</span>
                <div>
                  <strong>Faculty Double-Booking:</strong>
                  <div className="constraint-detail">No faculty member may teach multiple classes simultaneously</div>
                </div>
              </div>
              <div className="constraint-meta">
                <span className="weight-tag">Weight: 1,000</span>
                <span className={`metric-badge ${c.faculty_conflicts === 0 ? "zero" : "viol"}`}>
                  {c.faculty_conflicts === 0 ? "0 conflicts" : `${c.faculty_conflicts} conflicts`}
                </span>
              </div>
            </li>

            <li className="constraint-item">
              <div className="constraint-desc">
                <span className="check-icon">{c.student_conflicts === 0 ? "✓" : "✗"}</span>
                <div>
                  <strong>Student/Batch Double-Booking:</strong>
                  <div className="constraint-detail">A batch cannot attend two concurrent sessions in the same period</div>
                </div>
              </div>
              <div className="constraint-meta">
                <span className="weight-tag">Weight: 1,000</span>
                <span className={`metric-badge ${c.student_conflicts === 0 ? "zero" : "viol"}`}>
                  {c.student_conflicts === 0 ? "0 conflicts" : `${c.student_conflicts} conflicts`}
                </span>
              </div>
            </li>

            <li className="constraint-item">
              <div className="constraint-desc">
                <span className="check-icon">{c.room_conflicts === 0 ? "✓" : "✗"}</span>
                <div>
                  <strong>Room Double-Booking:</strong>
                  <div className="constraint-detail">A classroom or lab cannot host two different sessions simultaneously</div>
                </div>
              </div>
              <div className="constraint-meta">
                <span className="weight-tag">Weight: 1,000</span>
                <span className={`metric-badge ${c.room_conflicts === 0 ? "zero" : "viol"}`}>
                  {c.room_conflicts === 0 ? "0 conflicts" : `${c.room_conflicts} conflicts`}
                </span>
              </div>
            </li>

            <li className="constraint-item">
              <div className="constraint-desc">
                <span className="check-icon">{c.capacity_violations === 0 ? "✓" : "✗"}</span>
                <div>
                  <strong>Room Capacity Violations:</strong>
                  <div className="constraint-detail">Assigned room capacity must equal or exceed batch student count</div>
                </div>
              </div>
              <div className="constraint-meta">
                <span className="weight-tag">Weight: 500</span>
                <span className={`metric-badge ${c.capacity_violations === 0 ? "zero" : "viol"}`}>
                  {c.capacity_violations === 0 ? "0 violations" : `${c.capacity_violations} violations`}
                </span>
              </div>
            </li>
          </ul>
        </div>

        {/* SOFT CONSTRAINTS */}
        <div className="constraint-block soft-block">
          <div className="constraint-block-header">
            <h3>Soft Constraints (Optimization Preferences)</h3>
            <span className="constraint-status-tag warning">
              {softTotal} Total Penalties
            </span>
          </div>
          <ul className="constraint-items">
            <li className="constraint-item">
              <div className="constraint-desc">
                <span className="check-icon neutral">○</span>
                <div>
                  <strong>Faculty Idle-Period Gaps:</strong>
                  <div className="constraint-detail">Unassigned idle periods between a professor's first and last class on a day</div>
                </div>
              </div>
              <div className="constraint-meta">
                <span className="weight-tag">Weight: 10</span>
                <span className="metric-badge soft-badge">
                  {c.faculty_gaps} gaps
                </span>
              </div>
            </li>

            <li className="constraint-item">
              <div className="constraint-desc">
                <span className="check-icon neutral">○</span>
                <div>
                  <strong>Student/Batch Idle-Period Gaps:</strong>
                  <div className="constraint-detail">Unoccupied periods between a batch's scheduled classes in a daily timetable</div>
                </div>
              </div>
              <div className="constraint-meta">
                <span className="weight-tag">Weight: 10</span>
                <span className="metric-badge soft-badge">
                  {c.student_gaps} gaps
                </span>
              </div>
            </li>

            <li className="constraint-item">
              <div className="constraint-desc">
                <span className="check-icon neutral">○</span>
                <div>
                  <strong>Weekly Subject Distribution:</strong>
                  <div className="constraint-detail">Penalizes clustering a subject's multiple weekly sessions on the same day</div>
                </div>
              </div>
              <div className="constraint-meta">
                <span className="weight-tag">Weight: 5</span>
                <span className="metric-badge soft-badge">
                  {distributionPenalties} penalties
                </span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

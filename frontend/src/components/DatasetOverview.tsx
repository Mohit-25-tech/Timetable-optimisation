import type { DatasetInput } from "../types";

interface Props {
  dataset: DatasetInput;
}

export default function DatasetOverview({ dataset }: Props) {
  const totalSessions = dataset.subjects.reduce((sum, s) => sum + s.sessions_per_week, 0);
  const totalSlots = dataset.days.length * dataset.periods_per_day * dataset.rooms.length;

  return (
    <div className="card dataset-card">
      <div className="card-header-row">
        <h2>Problem Formulation &amp; Dataset</h2>
        <span className="dataset-tag">Academic Benchmark Dataset</span>
      </div>

      <div className="stat-row" style={{ marginBottom: 16 }}>
        <div className="stat">
          <div className="value">{dataset.subjects.length}</div>
          <div className="label">Subjects</div>
        </div>
        <div className="stat">
          <div className="value">{dataset.faculty.length}</div>
          <div className="label">Faculty Members</div>
        </div>
        <div className="stat">
          <div className="value">{dataset.rooms.length}</div>
          <div className="label">Available Rooms</div>
        </div>
        <div className="stat">
          <div className="value">{dataset.batches.length}</div>
          <div className="label">Student Batches</div>
        </div>
        <div className="stat">
          <div className="value">{totalSessions}</div>
          <div className="label">Sessions/Week Required</div>
        </div>
        <div className="stat">
          <div className="value">{totalSlots}</div>
          <div className="label">Room-Period Slots</div>
        </div>
      </div>

      <div className="problem-formulation-box">
        <p className="formulation-text">
          <strong>Scheduling Problem:</strong> <strong>{totalSessions} class sessions</strong> must be assigned across available days,
          periods, and rooms while satisfying faculty, student/batch, room conflict, and room capacity constraints.
        </p>
        <div className="formulation-details">
          <div className="detail-item">
            <span className="detail-bullet">•</span>
            <span>
              <strong>Curriculum Requirement:</strong> {dataset.subjects.length} subjects requiring a total of{" "}
              <strong>{totalSessions} weekly sessions</strong> (averaging 3 sessions/subject: 10 subjects × 3 sessions + 10 subjects × 2 sessions + 10 subjects × 4 sessions = 90 sessions).
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-bullet">•</span>
            <span>
              <strong>Search Space:</strong> {dataset.days.length} days × {dataset.periods_per_day} periods × {dataset.rooms.length} rooms ={" "}
              <strong>{totalSlots} room-period slots</strong> available across the university. The Genetic Algorithm must place all {totalSessions} sessions without conflicts.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

import { useMemo, useState } from "react";
import type { GeneOut } from "../types";

interface Props {
  timetable: GeneOut[];
  days: string[];
  periodsPerDay: number;
  onExport: () => void;
  exporting: boolean;
}

const DAY_DISPLAY_NAMES: Record<string, string> = {
  Mon: "Monday",
  Tue: "Tuesday",
  Wed: "Wednesday",
  Thu: "Thursday",
  Fri: "Friday",
};

export default function TimetableView({
  timetable,
  days,
  periodsPerDay,
  onExport,
  exporting,
}: Props) {
  const [dayFilter, setDayFilter] = useState("all");
  const [batchFilter, setBatchFilter] = useState("all");
  const [facultyFilter, setFacultyFilter] = useState("all");
  const [roomFilter, setRoomFilter] = useState("all");

  const batches = useMemo(
    () => uniqueBy(timetable, (g) => [g.batch_id, g.batch_name]),
    [timetable]
  );
  const faculty = useMemo(
    () => uniqueBy(timetable, (g) => [g.faculty_id, g.faculty_name]),
    [timetable]
  );
  const rooms = useMemo(
    () => uniqueBy(timetable, (g) => [g.room_id, g.room_number]),
    [timetable]
  );

  // Apply filters
  const filtered = useMemo(() => {
    return timetable.filter(
      (g) =>
        (dayFilter === "all" || g.day === dayFilter) &&
        (batchFilter === "all" || g.batch_id === batchFilter) &&
        (facultyFilter === "all" || g.faculty_id === facultyFilter) &&
        (roomFilter === "all" || g.room_id === roomFilter)
    );
  }, [timetable, dayFilter, batchFilter, facultyFilter, roomFilter]);

  // Determine which day columns to display in table header & body
  const visibleDays = dayFilter === "all" ? days : [dayFilter];

  // Group filtered sessions by day and period
  const grid = useMemo(() => {
    const map: Record<string, Record<number, GeneOut[]>> = {};
    for (const d of visibleDays) {
      map[d] = {};
    }
    for (const g of filtered) {
      if (!map[g.day]) map[g.day] = {};
      if (!map[g.day][g.period]) map[g.day][g.period] = [];
      map[g.day][g.period].push(g);
    }
    return map;
  }, [filtered, visibleDays]);

  return (
    <div className="card timetable-card">
      <div className="card-header-row">
        <h2>Optimized Academic Timetable</h2>
        <div className="timetable-actions">
          <button
            type="button"
            className="secondary-btn export-btn"
            onClick={onExport}
            disabled={exporting}
            title="Download full schedule as CSV"
          >
            {exporting ? "Generating CSV…" : "↓ Export CSV"}
          </button>
        </div>
      </div>

      {/* FILTER BAR */}
      <div className="filters-toolbar">
        <div className="filter-group">
          <label htmlFor="filter-day">Day:</label>
          <select
            id="filter-day"
            value={dayFilter}
            onChange={(e) => setDayFilter(e.target.value)}
          >
            <option value="all">All Days</option>
            {days.map((d) => (
              <option key={d} value={d}>
                {DAY_DISPLAY_NAMES[d] ?? d}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-batch">Batch:</label>
          <select
            id="filter-batch"
            value={batchFilter}
            onChange={(e) => setBatchFilter(e.target.value)}
          >
            <option value="all">All Batches</option>
            {batches.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-faculty">Faculty:</label>
          <select
            id="filter-faculty"
            value={facultyFilter}
            onChange={(e) => setFacultyFilter(e.target.value)}
          >
            <option value="all">All Faculty</option>
            {faculty.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-room">Room:</label>
          <select
            id="filter-room"
            value={roomFilter}
            onChange={(e) => setRoomFilter(e.target.value)}
          >
            <option value="all">All Rooms</option>
            {rooms.map(([id, name]) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </select>
        </div>

        {(dayFilter !== "all" || batchFilter !== "all" || facultyFilter !== "all" || roomFilter !== "all") && (
          <button
            type="button"
            className="clear-filters-btn"
            onClick={() => {
              setDayFilter("all");
              setBatchFilter("all");
              setFacultyFilter("all");
              setRoomFilter("all");
            }}
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* FILTER RESULT COUNT TEXT */}
      <div className="filter-count-status">
        Showing <strong>{filtered.length}</strong> of <strong>{timetable.length}</strong> sessions matching the current filters.
      </div>

      {/* TIMETABLE GRID */}
      <div className="table-responsive-container">
        <table className="academic-timetable-table">
          <thead>
            <tr>
              <th className="period-col-header">Period</th>
              {visibleDays.map((d) => (
                <th key={d} className="day-col-header">
                  {DAY_DISPLAY_NAMES[d] ?? d}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: periodsPerDay }, (_, i) => i + 1).map((period) => (
              <tr key={period}>
                <td className="period-cell">
                  <div className="period-label">Period {period}</div>
                  <div className="period-time-sub">Slot {period}</div>
                </td>
                {visibleDays.map((day) => {
                  const sessions = grid[day]?.[period] ?? [];
                  return (
                    <td key={day} className="slot-cell">
                      {sessions.length === 0 ? (
                        <div className="empty-slot">—</div>
                      ) : (
                        <div className="sessions-stack">
                          {sessions.map((g) => (
                            <div
                              key={`${g.subject_id}-${g.batch_id}-${period}-${day}`}
                              className="session-card"
                            >
                              <div className="session-subject">{g.subject_name}</div>
                              <div className="session-faculty">{g.faculty_name}</div>
                              <div className="session-meta">
                                <span className="meta-pill batch-pill">{g.batch_name}</span>
                                <span className="meta-sep">·</span>
                                <span className="meta-pill room-pill">{g.room_number}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function uniqueBy(items: GeneOut[], keyFn: (g: GeneOut) => [string, string]): [string, string][] {
  const map = new Map<string, string>();
  for (const item of items) {
    const [id, name] = keyFn(item);
    map.set(id, name);
  }
  return Array.from(map.entries()).sort((a, b) => a[1].localeCompare(b[1]));
}

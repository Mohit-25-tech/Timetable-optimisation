import { useEffect, useState } from "react";
import { checkHealth, exportCsv, fetchDemoData, runOptimize } from "./api";
import type { DatasetInput, GAConfig, OptimizeResponse } from "./types";
import { DEFAULT_CONFIG } from "./types";
import DatasetOverview from "./components/DatasetOverview";
import ConfigPanel from "./components/ConfigPanel";
import OptimizationResult from "./components/OptimizationResult";
import ConvergenceCharts from "./components/ConvergenceCharts";
import ConstraintPanel from "./components/ConstraintPanel";
import TimetableView from "./components/TimetableView";
import RunSummary from "./components/RunSummary";
import AlgorithmExplainer from "./components/AlgorithmExplainer";

type BackendStatus = "checking" | "up" | "down";

export default function App() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");
  const [dataset, setDataset] = useState<DatasetInput | null>(null);
  const [config, setConfig] = useState<GAConfig>(DEFAULT_CONFIG);
  const [result, setResult] = useState<OptimizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkHealth().then((up) => setBackendStatus(up ? "up" : "down"));
  }, []);

  useEffect(() => {
    if (backendStatus !== "up" || dataset) return;
    fetchDemoData()
      .then(setDataset)
      .catch((e) => setError(String(e)));
  }, [backendStatus, dataset]);

  async function handleOptimize() {
    if (!dataset) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runOptimize(dataset, config);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleExport() {
    if (!result) return;
    setExporting(true);
    try {
      const csv = await exportCsv(result.timetable);
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `academic_timetable_gen_${result.generations_executed}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="header-branding">
          <div className="institution-tag">Academic Combinatorial Optimization Dashboard</div>
          <h1>University Timetable Optimizer</h1>
          <p className="header-subtitle">
            Constraint-Aware Genetic Algorithm for Conflict-Free Curriculum Scheduling
          </p>
        </div>
        <div className="header-status-area">
          <span
            className={`status-pill ${
              backendStatus === "up" ? "ok" : backendStatus === "down" ? "down" : ""
            }`}
          >
            {backendStatus === "checking" && "Checking backend…"}
            {backendStatus === "up" && "● FastAPI Backend Connected (Port 8000)"}
            {backendStatus === "down" && "● Backend Unavailable"}
          </span>
        </div>
      </header>

      {backendStatus === "down" && (
        <div className="error-state">
          <h3>Backend Server Not Responding</h3>
          <p>
            The FastAPI backend is currently unavailable. Please ensure it is running from the project root:
          </p>
          <pre className="code-block">uvicorn backend.main:app --reload</pre>
          <p style={{ marginTop: 10 }}>Then refresh this browser page.</p>
        </div>
      )}

      {backendStatus === "up" && (
        <>
          {/* Section 4: Problem Formulation & Dataset Statistics */}
          {dataset ? (
            <DatasetOverview dataset={dataset} />
          ) : (
            <div className="card loading-card">Loading benchmark dataset…</div>
          )}

          {/* GA Hyperparameter Configuration Panel */}
          <ConfigPanel config={config} onChange={setConfig} disabled={loading} />

          {/* Action Toolbar */}
          <div className="action-toolbar">
            <button
              type="button"
              className="primary-optimize-btn"
              onClick={handleOptimize}
              disabled={loading || !dataset}
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  Evolving Population (Running Genetic Algorithm…)
                </>
              ) : (
                <>▶ Run Genetic Algorithm Optimization</>
              )}
            </button>
            <span className="toolbar-hint">
              Assigns 90 sessions across 300 room-period slots while resolving all hard collisions.
            </span>
          </div>

          {loading && (
            <div className="card running-state-card">
              <div className="running-indicator">
                <span className="pulsing-dot" />
                <div>
                  <strong>Executing Optimization Pipeline…</strong>
                  <div className="running-subtext">
                    Evaluating chromosomes · Applying tournament selection (K={config.tournament_size}) · Recombining via two-point crossover · Mutating slots · Performing bounded constraint repair
                  </div>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="error-state" style={{ marginBottom: 20 }}>
              <strong>Execution Error:</strong> {error}
            </div>
          )}

          {!result && !loading && !error && (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>Ready for Optimization</h3>
              <p>
                The curriculum dataset is loaded with 30 subjects, 20 faculty, 10 rooms, and 5 batches (90 total sessions).
                Adjust parameters above if desired, then click <strong>"Run Genetic Algorithm Optimization"</strong> to evolve the schedule.
              </p>
            </div>
          )}

          {/* Optimization Results */}
          {result && dataset && (
            <>
              {/* Section 1 & 2: Prominent Optimization Result & Before vs After Improvement */}
              <OptimizationResult result={result} />

              {/* Section 3: Dual Convergence Charts (Fitness vs Gen & Cost vs Gen) */}
              <ConvergenceCharts history={result.history} />

              {/* Section 5: Hard vs Soft Constraint Analysis */}
              <ConstraintPanel result={result} />

              {/* Section 6 & 7: Optimized Timetable with Fixed Filters and Academic Styling */}
              <TimetableView
                timetable={result.timetable}
                days={dataset.days}
                periodsPerDay={dataset.periods_per_day}
                onExport={handleExport}
                exporting={exporting}
              />

              {/* Section 12: Compact Run Summary */}
              <RunSummary result={result} config={config} dataset={dataset} />
            </>
          )}

          {/* Section 8, 9, 10, 11: Educational Pipeline & Viva Explanations */}
          <AlgorithmExplainer config={config} />
        </>
      )}

      <footer className="app-footer">
        <p>
          University Course Timetable Optimizer · Constraint-Aware Genetic Algorithm implemented from scratch in Python.
        </p>
        <p className="sub-footer">
          Academic Research Prototype · Zero Black-Box Solver Dependencies · Discrete Combinatorial Optimization
        </p>
      </footer>
    </div>
  );
}

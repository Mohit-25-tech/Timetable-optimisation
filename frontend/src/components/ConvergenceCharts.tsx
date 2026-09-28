import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { GenerationStat } from "../types";

interface Props {
  history: GenerationStat[];
}

export default function ConvergenceCharts({ history }: Props) {
  if (history.length === 0) return null;

  return (
    <div className="card convergence-card">
      <div className="card-header-row">
        <h2>Algorithm Convergence Dynamics</h2>
        <span className="dataset-tag">{history.length} Generations Logged</span>
      </div>

      <div className="charts-grid">
        {/* Chart 1: Fitness vs Generation */}
        <div className="chart-container">
          <div className="chart-header">
            <h3>Fitness vs. Generation</h3>
            <p className="chart-explanation">
              <strong>Observation:</strong> Fitness increases as the population improves and evolves toward higher-quality solutions.
            </p>
          </div>
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <LineChart data={history} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6e4df" />
                <XAxis
                  dataKey="generation"
                  tick={{ fontSize: 11 }}
                  label={{ value: "Generation", position: "insideBottom", offset: -12, fontSize: 11, fill: "#5b6560" }}
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v: number) => v.toFixed(5)}
                  label={{ value: "Fitness Score", angle: -90, position: "insideLeft", offset: -4, fontSize: 11, fill: "#5b6560" }}
                />
                <Tooltip
                  formatter={(val: number) => [val.toFixed(6), ""]}
                  labelFormatter={(gen) => `Generation ${gen}`}
                  contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e0da", fontSize: 12, borderRadius: 4 }}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 6 }} />
                <Line
                  type="monotone"
                  dataKey="best_fitness"
                  name="Best Fitness"
                  stroke="#2f5233"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="avg_fitness"
                  name="Average Fitness"
                  stroke="#8a6d1e"
                  strokeWidth={1.5}
                  strokeDasharray="4 3"
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Cost vs Generation */}
        <div className="chart-container">
          <div className="chart-header">
            <h3>Cost vs. Generation</h3>
            <p className="chart-explanation">
              <strong>Observation:</strong> Cost decreases as constraint violations and idle gap penalties are systematically resolved.
            </p>
          </div>
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <LineChart data={history} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e6e4df" />
                <XAxis
                  dataKey="generation"
                  tick={{ fontSize: 11 }}
                  label={{ value: "Generation", position: "insideBottom", offset: -12, fontSize: 11, fill: "#5b6560" }}
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v: number) => v.toLocaleString()}
                  label={{ value: "Total Objective Cost", angle: -90, position: "insideLeft", offset: -4, fontSize: 11, fill: "#5b6560" }}
                />
                <Tooltip
                  formatter={(val: number) => [val.toLocaleString(undefined, { maximumFractionDigits: 1 }), ""]}
                  labelFormatter={(gen) => `Generation ${gen}`}
                  contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e0da", fontSize: 12, borderRadius: 4 }}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 6 }} />
                <Line
                  type="monotone"
                  dataKey="best_cost"
                  name="Best Cost (Objective Penalty)"
                  stroke="#9c3b3b"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

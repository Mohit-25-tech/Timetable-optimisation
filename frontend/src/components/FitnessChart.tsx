import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import type { GenerationStat } from "../types";

export default function FitnessChart({ history }: { history: GenerationStat[] }) {
  if (history.length === 0) return null;

  return (
    <div className="card">
      <h2>Fitness &amp; Cost Convergence</h2>
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          <LineChart data={history} margin={{ top: 8, right: 24, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e0da" />
            <XAxis dataKey="generation" tick={{ fontSize: 11 }} label={{ value: "Generation", position: "insideBottom", offset: -2, fontSize: 11 }} />
            <YAxis yAxisId="fitness" tick={{ fontSize: 11 }} label={{ value: "Fitness", angle: -90, position: "insideLeft", fontSize: 11 }} />
            <YAxis yAxisId="cost" orientation="right" tick={{ fontSize: 11 }} label={{ value: "Cost", angle: 90, position: "insideRight", fontSize: 11 }} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line yAxisId="fitness" type="monotone" dataKey="best_fitness" name="Best fitness" stroke="#2f5233" dot={false} strokeWidth={2} />
            <Line yAxisId="fitness" type="monotone" dataKey="avg_fitness" name="Avg fitness" stroke="#8a6d1e" dot={false} strokeWidth={1.5} strokeDasharray="4 3" />
            <Line yAxisId="cost" type="monotone" dataKey="best_cost" name="Best cost" stroke="#9c3b3b" dot={false} strokeWidth={1.5} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

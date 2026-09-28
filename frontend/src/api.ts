import type { DatasetInput, GAConfig, OptimizeResponse, GeneOut } from "./types";

const BASE_URL = "http://localhost:8000";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore parse failure, fall back to statusText
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function fetchDemoData(): Promise<DatasetInput> {
  const res = await fetch(`${BASE_URL}/api/demo-data`);
  return handle<DatasetInput>(res);
}

export async function runOptimize(dataset: DatasetInput, config: GAConfig): Promise<OptimizeResponse> {
  const res = await fetch(`${BASE_URL}/api/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset, config }),
  });
  return handle<OptimizeResponse>(res);
}

export async function exportCsv(timetable: GeneOut[]): Promise<string> {
  const res = await fetch(`${BASE_URL}/api/export/csv`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ timetable }),
  });
  if (!res.ok) throw new Error("Export failed");
  return res.text();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/health`);
    return res.ok;
  } catch {
    return false;
  }
}

import type {
  CreateSimulationRequest,
  MapInfo,
  Metrics,
  RobotState,
  SimulationInfo,
  TaskRow,
} from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return (await res.json()) as T;
}

const post = <T,>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  createSimulation: (req: CreateSimulationRequest) => post<SimulationInfo>("/api/v1/simulations", req),
  listSimulations: () => request<SimulationInfo[]>("/api/v1/simulations"),
  getSimulation: (id: string) => request<SimulationInfo>(`/api/v1/simulations/${id}`),
  start: (id: string) => post<SimulationInfo>(`/api/v1/simulations/${id}/start`),
  pause: (id: string) => post<SimulationInfo>(`/api/v1/simulations/${id}/pause`),
  reset: (id: string) => post<SimulationInfo>(`/api/v1/simulations/${id}/reset`),
  map: (id: string) => request<MapInfo>(`/api/v1/simulations/${id}/map`),
  robots: (id: string) => request<RobotState[]>(`/api/v1/robots?simulation_id=${id}`),
  tasks: (id: string) => request<TaskRow[]>(`/api/v1/tasks?simulation_id=${id}`),
  metrics: (id: string) =>
    request<{ simulation_id: string; metrics: Metrics }>(`/api/v1/metrics/${id}`).then((r) => r.metrics),
  startExperiment: (spec: string, profile: "quick" | "full") => post<Record<string, unknown>>("/api/v1/experiments", { spec, profile }),
  experimentSpecs: () => request<string[]>("/api/v1/experiments/specs"),
  experiments: () => request<Record<string, unknown>[]>("/api/v1/experiments"),
};

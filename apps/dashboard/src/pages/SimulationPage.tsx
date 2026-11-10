import { useEffect, useState } from "react";

import { useSimulation } from "../app/SimulationContext";
import { WarehouseCanvas } from "../components/simulation/WarehouseCanvas";
import { api } from "../services/api";
import type { CreateSimulationRequest } from "../types";

export function SimulationPage() {
  const { simulationId, setSimulationId, frame, map } = useSimulation();
  const [form, setForm] = useState<CreateSimulationRequest>({
    scenario: "warehouse_small", robot_count: 10, allocation_algorithm: "hungarian",
    planning_algorithm: "astar", seed: 42,
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => setError(null), [form]);

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };
  const set = <K extends keyof CreateSimulationRequest>(k: K, v: CreateSimulationRequest[K]) => setForm({ ...form, [k]: v });

  return (
    <>
      {error && <div className="banner error">{error}</div>}
      <div className="controls">
        <label>Environment
          <select value={form.scenario} onChange={(e) => set("scenario", e.target.value)}>
            <option value="warehouse_small">small (20×20)</option>
            <option value="warehouse_medium">medium (40×30)</option>
            <option value="warehouse_large">large (60×40)</option>
          </select>
        </label>
        <label>Robots
          <input type="number" min={1} max={200} value={form.robot_count} onChange={(e) => set("robot_count", Number(e.target.value))} />
        </label>
        <label>Allocation
          <select value={form.allocation_algorithm} onChange={(e) => set("allocation_algorithm", e.target.value as CreateSimulationRequest["allocation_algorithm"])}>
            <option>hungarian</option><option>auction</option><option>greedy</option>
          </select>
        </label>
        <label>Planning
          <select value={form.planning_algorithm} onChange={(e) => set("planning_algorithm", e.target.value as CreateSimulationRequest["planning_algorithm"])}>
            <option>astar</option><option>dijkstra</option><option>cbs</option>
          </select>
        </label>
        <label>Seed
          <input type="number" min={0} value={form.seed} onChange={(e) => set("seed", Number(e.target.value))} />
        </label>
        <button disabled={busy} onClick={() => run(async () => setSimulationId((await api.createSimulation(form)).simulation_id))}>Create</button>
        <button disabled={busy || !simulationId} onClick={() => run(() => api.start(simulationId!))}>Start / Resume</button>
        <button disabled={busy || !simulationId} onClick={() => run(() => api.pause(simulationId!))}>Pause</button>
        <button disabled={busy || !simulationId} onClick={() => run(() => api.reset(simulationId!))}>Reset</button>
      </div>
      {simulationId && <p>{simulationId} – {frame?.status ?? "…"} – t = {frame?.simulation_time.toFixed(1) ?? "0.0"} s</p>}
      <WarehouseCanvas map={map} robots={frame?.robots ?? []} />
    </>
  );
}

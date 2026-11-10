import { useEffect, useState } from "react";

import { useSimulation } from "../app/SimulationContext";
import { MetricCards } from "../components/analytics/MetricCards";
import { MetricsBarChart } from "../components/charts/MetricsBarChart";
import { api } from "../services/api";
import type { Metrics } from "../types";
import { fmtNumber } from "../utils/format";

export function AnalyticsPage() {
  const { simulationId, frame } = useSimulation();
  const [m, setM] = useState<Metrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!simulationId) return;
    api.metrics(simulationId).then(setM).catch((e) => setError(String(e)));
  }, [simulationId, frame?.completed_tasks, frame?.status]);

  if (!simulationId) return <p>Create a simulation first.</p>;
  if (!m) return <p>{error ?? "Loading metrics…"}</p>;
  return (
    <>
      <MetricCards items={[
        { label: "Completion rate (%)", value: fmtNumber(m.task_completion_rate, 1) },
        { label: "Throughput (tasks/s)", value: fmtNumber(m.throughput, 3) },
        { label: "Avg completion time (s)", value: fmtNumber(m.average_completion_time, 1) },
        { label: "Travel distance (m)", value: fmtNumber(m.total_distance, 0) },
        { label: "Idle time (robot-s)", value: fmtNumber(m.idle_time, 0) },
        { label: "Planning runtime (ms)", value: fmtNumber(m.planning_runtime_ms, 1) },
        { label: "Energy consumption", value: fmtNumber(m.energy_total, 0) },
        { label: "Collision events", value: fmtNumber(m.collision_count, 0) },
      ]} />
      <MetricsBarChart title="Safety events" data={[
        { name: "collisions", value: Number(m.collision_count ?? 0) },
        { name: "safety violations", value: Number(m.safety_violations ?? 0) },
        { name: "potential", value: Number(m.potential_collisions ?? 0) },
        { name: "deadlocks", value: Number(m.deadlock_events ?? 0) },
      ]} />
    </>
  );
}

import { MetricCards } from "../components/analytics/MetricCards";
import { useSimulation } from "../app/SimulationContext";
import { countByStatus, formatDuration } from "../utils/format";

export function OverviewPage() {
  const { frame, simulationId } = useSimulation();
  if (!simulationId) return <p>Create a simulation on the Simulation page to see fleet statistics.</p>;
  if (!frame) return <p>Waiting for the first frame…</p>;
  const by = countByStatus(frame.robots);
  const total = frame.robots.length;
  const unavailable = by["unavailable"] ?? 0;
  const active = (by["moving"] ?? 0) + (by["executing"] ?? 0);
  const throughput = frame.simulation_time > 0 ? (frame.completed_tasks / frame.simulation_time) * 60 : 0;
  return (
    <MetricCards
      items={[
        { label: "Total robots", value: String(total) },
        { label: "Available robots", value: String(total - unavailable) },
        { label: "Active robots", value: String(active) },
        { label: "Unavailable robots", value: String(unavailable) },
        { label: "Active tasks", value: String(frame.pending_tasks) },
        { label: "Completed tasks", value: String(frame.completed_tasks) },
        { label: "Throughput (tasks/min)", value: throughput.toFixed(2) },
        { label: "Simulation time", value: formatDuration(frame.simulation_time) },
      ]}
    />
  );
}

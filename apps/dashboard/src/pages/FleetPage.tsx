import { useSimulation } from "../app/SimulationContext";
import { FleetTable } from "../components/fleet/FleetTable";

export function FleetPage() {
  const { frame } = useSimulation();
  return frame ? <FleetTable robots={frame.robots} /> : <p>No live data yet.</p>;
}

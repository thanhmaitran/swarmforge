import type { ConnectionState } from "../../hooks/useSimulationStream";
import type { Frame } from "../../types";

interface Props {
  state: ConnectionState;
  simulationStatus: Frame["status"] | null;
}

export function ConnectionBanner({ state, simulationStatus }: Props) {
  if (simulationStatus === "completed") return null;

  if (simulationStatus === "failed") {
    return <div className="banner error">Simulation failed. Check the simulation details and API logs.</div>;
  }

  if (state === "open" || state === "idle") return null;

  const text =
    state === "connecting"
      ? "Connecting to simulation stream..."
      : "Disconnected from the simulation stream - retrying.";

  return <div className="banner error">{text}</div>;
}

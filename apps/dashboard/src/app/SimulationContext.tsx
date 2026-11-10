import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { useSimulationStream, type ConnectionState } from "../hooks/useSimulationStream";
import { api } from "../services/api";
import type { Frame, MapInfo } from "../types";

interface Ctx {
  simulationId: string | null;
  setSimulationId: (id: string | null) => void;
  frame: Frame | null;
  connection: ConnectionState;
  map: MapInfo | null;
}

const SimulationContext = createContext<Ctx | null>(null);

export function SimulationProvider({ children }: { children: ReactNode }) {
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [map, setMap] = useState<MapInfo | null>(null);
  const { frame, state } = useSimulationStream(simulationId);

  useEffect(() => {
    if (!simulationId) {
      setMap(null);
      return;
    }
    api.map(simulationId).then(setMap).catch(() => setMap(null));
  }, [simulationId]);

  return (
    <SimulationContext.Provider value={{ simulationId, setSimulationId, frame, connection: state, map }}>
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulation(): Ctx {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error("useSimulation must be used inside <SimulationProvider>");
  return ctx;
}

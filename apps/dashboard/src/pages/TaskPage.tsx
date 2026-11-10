import { useEffect, useState } from "react";

import { useSimulation } from "../app/SimulationContext";
import { TaskTable } from "../components/tasks/TaskTable";
import { api } from "../services/api";
import type { TaskRow } from "../types";

export function TaskPage() {
  const { simulationId, frame } = useSimulation();
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!simulationId) return;
    api.tasks(simulationId).then(setTasks).catch((e) => setError(String(e)));
  }, [simulationId, frame?.completed_tasks, frame?.pending_tasks]);

  if (!simulationId) return <p>Create a simulation first.</p>;
  return (
    <>
      {error && <div className="banner error">{error}</div>}
      <TaskTable tasks={tasks} />
    </>
  );
}

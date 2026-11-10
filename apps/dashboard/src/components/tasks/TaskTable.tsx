import type { TaskRow } from "../../types";

export function TaskTable({ tasks }: { tasks: TaskRow[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Task</th><th>Priority</th><th>Pickup</th><th>Destination</th><th>Robot</th><th>Status</th><th>Deadline (s)</th>
        </tr>
      </thead>
      <tbody>
        {tasks.map((t) => (
          <tr key={t.task_id}>
            <td>{t.task_id}</td>
            <td>{t.priority}</td>
            <td>{t.pickup.join(", ")}</td>
            <td>{t.destination.join(", ")}</td>
            <td>{t.assigned_robot_id ?? "–"}</td>
            <td>{t.status}</td>
            <td>{t.deadline?.toFixed(0) ?? "–"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

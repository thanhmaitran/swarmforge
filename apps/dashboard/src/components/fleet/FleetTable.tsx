import type { RobotState } from "../../types";
import { STATUS_COLORS } from "../../utils/format";

export function FleetTable({ robots }: { robots: RobotState[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Robot</th><th>Status</th><th>Position (m)</th><th>Heading (rad)</th><th>Battery</th><th>Task</th>
        </tr>
      </thead>
      <tbody>
        {robots.map((r) => (
          <tr key={r.robot_id}>
            <td>{r.robot_id}</td>
            <td style={{ color: STATUS_COLORS[r.status] }}>{r.status}</td>
            <td>{r.x.toFixed(1)}, {r.y.toFixed(1)}</td>
            <td>{r.orientation.toFixed(2)}</td>
            <td>{r.battery.toFixed(0)}%</td>
            <td>{r.task_id ?? "–"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

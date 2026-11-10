import type { RobotState } from "../types";

export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "–";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s.toString().padStart(2, "0")}s` : `${s}s`;
}

export const STATUS_COLORS: Record<RobotState["status"], string> = {
  idle: "#8a97a8",
  assigned: "#e0a800",
  moving: "#1f77b4",
  executing: "#2ca02c",
  charging: "#9467bd",
  unavailable: "#d62728",
};

export function countByStatus(robots: RobotState[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const r of robots) out[r.status] = (out[r.status] ?? 0) + 1;
  return out;
}

export function fmtNumber(v: unknown, digits = 2): string {
  return typeof v === "number" && Number.isFinite(v) ? v.toFixed(digits) : "–";
}

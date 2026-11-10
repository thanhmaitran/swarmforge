export interface RobotState {
  robot_id: string;
  x: number;
  y: number;
  orientation: number;
  status: "idle" | "assigned" | "moving" | "executing" | "charging" | "unavailable";
  battery: number;
  task_id: string | null;
  cell: [number, number];
}

export interface Frame {
  schema_version: number;
  simulation_id: string;
  simulation_time: number;
  status: "created" | "running" | "paused" | "completed" | "failed";
  robots: RobotState[];
  completed_tasks: number;
  pending_tasks: number;
}

export interface SimulationInfo {
  simulation_id: string;
  status: Frame["status"];
  simulation_time: number;
  termination_reason: string | null;
  request: Record<string, unknown>;
}

export interface TaskRow {
  task_id: string;
  priority: number;
  pickup: [number, number];
  destination: [number, number];
  status: string;
  assigned_robot_id: string | null;
  creation_time: number;
  deadline: number | null;
  completion_time: number | null;
}

export interface MapInfo {
  width: number;
  height: number;
  resolution: number;
  obstacles: [number, number][];
  pickup_zones: [number, number][];
  delivery_zones: [number, number][];
  charging_stations: [number, number][];
  spawn_zones: [number, number][];
}

export interface CreateSimulationRequest {
  scenario: string;
  robot_count: number;
  allocation_algorithm: "hungarian" | "auction" | "greedy";
  planning_algorithm: "dijkstra" | "astar" | "cbs";
  seed: number;
  task_count?: number;
}

export type Metrics = Record<string, number | string | null>;

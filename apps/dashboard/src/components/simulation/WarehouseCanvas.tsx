import { useEffect, useRef } from "react";

import type { MapInfo, RobotState } from "../../types";
import { STATUS_COLORS } from "../../utils/format";

const CELL = 18;

export function WarehouseCanvas({ map, robots }: { map: MapInfo | null; robots: RobotState[] }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !map) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const fill = (cells: [number, number][], color: string) => {
      ctx.fillStyle = color;
      for (const [x, y] of cells) ctx.fillRect(x * CELL, y * CELL, CELL, CELL);
    };
    fill(map.spawn_zones, "#eef1f5");
    fill(map.pickup_zones, "#d3e8ff");
    fill(map.delivery_zones, "#d9f2d9");
    fill(map.charging_stations, "#ffe3b3");
    fill(map.obstacles, "#5a6470");
    for (const r of robots) {
      const px = (r.x / map.resolution) * CELL;
      const py = (r.y / map.resolution) * CELL;
      ctx.beginPath();
      ctx.arc(px, py, CELL * 0.35, 0, 2 * Math.PI);
      ctx.fillStyle = STATUS_COLORS[r.status];
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(px, py);
      ctx.lineTo(px + Math.cos(r.orientation) * CELL * 0.45, py + Math.sin(r.orientation) * CELL * 0.45);
      ctx.strokeStyle = "#111";
      ctx.stroke();
    }
  }, [map, robots]);

  if (!map) return <p>No map loaded.</p>;
  return <canvas ref={ref} width={map.width * CELL} height={map.height * CELL} aria-label="warehouse view" />;
}

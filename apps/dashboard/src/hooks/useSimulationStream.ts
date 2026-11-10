import { useEffect, useRef, useState } from "react";

import type { Frame } from "../types";

export type ConnectionState = "idle" | "connecting" | "open" | "closed" | "error";

/** Streams frames for one simulation; reconnects with back-off until the run is finished. */
export function useSimulationStream(simulationId: string | null, rateHz = 5) {
  const [frame, setFrame] = useState<Frame | null>(null);
  const [state, setState] = useState<ConnectionState>("idle");
  const finished = useRef(false);

  useEffect(() => {
    if (!simulationId) {
      setState("idle");
      return;
    }
    finished.current = false;
    let ws: WebSocket | null = null;
    let retry = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let disposed = false;

    const connect = () => {
      setState("connecting");
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${window.location.host}/ws/simulations/${simulationId}?rate=${rateHz}`);
      ws.onopen = () => {
        retry = 0;
        setState("open");
      };
      ws.onmessage = (ev) => {
        const f = JSON.parse(ev.data) as Frame;
        if (f.schema_version !== 1) return; // unknown schema: ignore rather than crash
        setFrame(f);
        if (f.status === "completed" || f.status === "failed") finished.current = true;
      };
      ws.onerror = () => setState("error");
      ws.onclose = () => {
        setState("closed");
        if (!disposed && !finished.current) {
          timer = setTimeout(connect, Math.min(1000 * 2 ** retry++, 10000));
        }
      };
    };
    connect();
    return () => {
      disposed = true;
      if (timer) clearTimeout(timer);
      ws?.close();
    };
  }, [simulationId, rateHz]);

  return { frame, state };
}

import { describe, expect, it } from "vitest";

import { countByStatus, fmtNumber, formatDuration } from "../src/utils/format";

describe("format utils", () => {
  it("formats durations", () => {
    expect(formatDuration(5)).toBe("5s");
    expect(formatDuration(125)).toBe("2m 05s");
    expect(formatDuration(-1)).toBe("–");
    expect(formatDuration(Number.NaN)).toBe("–");
  });

  it("counts robots by status", () => {
    const robots = [
      { status: "idle" },
      { status: "idle" },
      { status: "moving" },
    ] as never[];
    expect(countByStatus(robots)).toEqual({ idle: 2, moving: 1 });
  });

  it("formats numbers defensively", () => {
    expect(fmtNumber(1.2345)).toBe("1.23");
    expect(fmtNumber(null)).toBe("–");
    expect(fmtNumber(undefined)).toBe("–");
  });
});

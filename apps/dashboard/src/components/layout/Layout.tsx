import type { ReactNode } from "react";

export type PageId = "overview" | "simulation" | "fleet" | "tasks" | "experiments" | "analytics";

const PAGES: { id: PageId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "simulation", label: "Simulation" },
  { id: "fleet", label: "Live Fleet" },
  { id: "tasks", label: "Tasks" },
  { id: "experiments", label: "Experiments" },
  { id: "analytics", label: "Analytics" },
];

export function Layout(props: { page: PageId; onNavigate: (p: PageId) => void; children: ReactNode }) {
  return (
    <>
      <header>
        <h1>SwarmForge</h1>
        <nav>
          {PAGES.map((p) => (
            <button key={p.id} className={p.id === props.page ? "active" : ""} onClick={() => props.onNavigate(p.id)}>
              {p.label}
            </button>
          ))}
        </nav>
      </header>
      <main>{props.children}</main>
    </>
  );
}

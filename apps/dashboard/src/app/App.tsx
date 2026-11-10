import { useState } from "react";

import { ConnectionBanner } from "../components/layout/ConnectionBanner";
import { Layout, type PageId } from "../components/layout/Layout";
import { AnalyticsPage } from "../pages/AnalyticsPage";
import { ExperimentsPage } from "../pages/ExperimentsPage";
import { FleetPage } from "../pages/FleetPage";
import { OverviewPage } from "../pages/OverviewPage";
import { SimulationPage } from "../pages/SimulationPage";
import { TaskPage } from "../pages/TaskPage";
import { SimulationProvider, useSimulation } from "./SimulationContext";

function Pages({ page }: { page: PageId }) {
  const { connection, frame } = useSimulation();

  return (
    <>
      <ConnectionBanner
        state={connection}
        simulationStatus={frame?.status ?? null}
      />
      {page === "overview" && <OverviewPage />}
      {page === "simulation" && <SimulationPage />}
      {page === "fleet" && <FleetPage />}
      {page === "tasks" && <TaskPage />}
      {page === "experiments" && <ExperimentsPage />}
      {page === "analytics" && <AnalyticsPage />}
    </>
  );
}

export function App() {
  const [page, setPage] = useState<PageId>("overview");

  return (
    <SimulationProvider>
      <Layout page={page} onNavigate={setPage}>
        <Pages page={page} />
      </Layout>
    </SimulationProvider>
  );
}

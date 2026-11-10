import { useEffect, useState } from "react";

import { api } from "../services/api";

export function ExperimentsPage() {
  const [specs, setSpecs] = useState<string[]>([]);
  const [spec, setSpec] = useState("");
  const [profile, setProfile] = useState<"quick" | "full">("quick");
  const [jobs, setJobs] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => api.experiments().then(setJobs).catch((e) => setError(String(e)));
  useEffect(() => {
    api.experimentSpecs().then((s) => { setSpecs(s); setSpec(s[0] ?? ""); }).catch((e) => setError(String(e)));
    refresh();
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, []);

  return (
    <>
      {error && <div className="banner error">{error}</div>}
      <div className="controls">
        <label>Experiment
          <select value={spec} onChange={(e) => setSpec(e.target.value)}>{specs.map((s) => <option key={s}>{s}</option>)}</select>
        </label>
        <label>Profile
          <select value={profile} onChange={(e) => setProfile(e.target.value as "quick" | "full")}><option>quick</option><option>full</option></select>
        </label>
        <button disabled={!spec} onClick={() => api.startExperiment(spec, profile).then(refresh).catch((e) => setError(String(e)))}>Run</button>
      </div>
      <p>Latency, packet-loss, task-arrival, obstacle and repetition settings are part of each experiment specification (see <code>experiments/scenarios/</code>).</p>
      <table>
        <thead><tr><th>ID</th><th>Spec</th><th>Profile</th><th>Runs</th><th>Status</th></tr></thead>
        <tbody>{jobs.map((j) => (
          <tr key={String(j.experiment_id)}><td>{String(j.experiment_id)}</td><td>{String(j.spec)}</td><td>{String(j.profile)}</td><td>{String(j.runs)}</td><td>{String(j.status)}</td></tr>
        ))}</tbody>
      </table>
    </>
  );
}

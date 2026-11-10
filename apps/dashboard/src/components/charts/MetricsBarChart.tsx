import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function MetricsBarChart({ data, title }: { data: { name: string; value: number }[]; title: string }) {
  return (
    <div className="card" style={{ height: 280 }}>
      <strong>{title}</strong>
      <ResponsiveContainer width="100%" height="90%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#1f77b4" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

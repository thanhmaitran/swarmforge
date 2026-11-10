export function MetricCards({ items }: { items: { label: string; value: string }[] }) {
  return (
    <div className="cards">
      {items.map((i) => (
        <div className="card" key={i.label}>
          <div className="value">{i.value}</div>
          <div className="label">{i.label}</div>
        </div>
      ))}
    </div>
  );
}

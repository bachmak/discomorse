interface Metric {
  label: string;
  unit: string;
}

const METRICS: Metric[] = [
  { label: "Speed", unit: "WPM" },
  { label: "Carrier", unit: "Hz" },
  { label: "Signal", unit: "dB" },
];

function MetricTile({ label, unit }: Metric) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <span className="metric-value" aria-hidden="true" />
      <span className="metric-unit">{unit}</span>
    </div>
  );
}

export function SignalMetrics() {
  return (
    <div className="metrics">
      {METRICS.map((metric) => (
        <MetricTile key={metric.label} {...metric} />
      ))}
    </div>
  );
}

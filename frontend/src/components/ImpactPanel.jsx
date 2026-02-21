function formatNumber(value) {
  if (typeof value !== "number") return String(value ?? "-");
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function tone(score) {
  if (score === null) return "badge-neutral";
  if (score >= 80) return "badge-success";
  if (score >= 60) return "badge-warning";
  return "badge-danger";
}

export default function ImpactPanel({ before, after, impactScore }) {
  const beforeEntries = Object.entries(before || {});
  const afterEntries = Object.entries(after || {});
  const keys = Array.from(new Set([...beforeEntries.map(([k]) => k), ...afterEntries.map(([k]) => k)]));

  return (
    <article className="card">
      <div className="cardHeader">
        <h2>Impact</h2>
        <span className={`badge ${tone(impactScore)}`}>Impact {impactScore === null ? "-" : `${impactScore}/100`}</span>
      </div>
      <div className="tableWrap">
        <table className="impactTable">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Before</th>
              <th>After</th>
            </tr>
          </thead>
          <tbody>
            {keys.length === 0 ? (
              <tr>
                <td colSpan={3} className="muted">No metrics yet.</td>
              </tr>
            ) : (
              keys.map((key) => (
                <tr key={key}>
                  <td className="mono">{key}</td>
                  <td>{formatNumber(before?.[key])}</td>
                  <td>{formatNumber(after?.[key])}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </article>
  );
}

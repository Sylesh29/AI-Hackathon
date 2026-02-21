export default function MemoryPanel({ entries, loading, error }) {
  return (
    <article className="card spanFull">
      <div className="cardHeader">
        <h2>Memory</h2>
      </div>
      {loading ? <div className="loadingBlock" /> : null}
      {error ? <p className="errorText">{error}</p> : null}
      {!loading && !error && entries.length === 0 ? <p className="muted">No learned patterns yet.</p> : null}
      {!loading && !error && entries.length > 0 ? (
        <div className="runList">
          {entries.map((entry, idx) => (
            <div className="runItem" key={`${entry.signature}-${idx}`}>
              <span className="mono">{entry.signature}</span>
              <span>{entry.fix}</span>
              <span>Outcome: {entry.outcome}</span>
              <span>Uses: {entry.uses}</span>
              <span>Last: {entry.last_used || "-"}</span>
            </div>
          ))}
        </div>
      ) : null}
    </article>
  );
}

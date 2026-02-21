function formatLogTime(ts) {
  if (!ts) return "--:--:--";
  return new Date(ts).toLocaleTimeString();
}

export default function LogsPanel({ logs, loading }) {
  return (
    <article className="card">
      <div className="cardHeader">
        <h2>Logs</h2>
      </div>
      <div className="logPanel" role="log" aria-live="polite">
        {loading ? <div className="loadingLine" /> : null}
        {!loading && logs.length === 0 ? <p className="muted">No logs yet.</p> : null}
        {logs.map((log, index) => (
          <div key={`${log.agent}-${index}-${log.timestamp || "na"}`} className="logRow">
            <span className="logTime mono">{formatLogTime(log.timestamp)}</span>
            <span className="badge badge-neutral mono">{log.agent}</span>
            <span className="logMessage">{log.message}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

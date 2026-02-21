function statusClass(kind) {
  if (kind === "ok") return "badge badge-success";
  if (kind === "warn") return "badge badge-warning";
  return "badge badge-danger";
}

export default function StatusBar({ statusLoading, statusInfo, pipelineLoading, autonomyInfo, statusError }) {
  const backendKind = statusLoading ? "warn" : statusInfo ? "ok" : "danger";
  const pipelineKind = pipelineLoading ? "warn" : "ok";
  const autonomyKind = autonomyInfo?.running ? "ok" : autonomyInfo?.enabled ? "warn" : "danger";

  return (
    <section className="statusBar" aria-label="System status">
      <span className={statusClass(backendKind)}>
        Backend: {statusLoading ? "Checking" : statusInfo ? `${statusInfo.status} (${Math.round(statusInfo.uptime_seconds)}s)` : "Unavailable"}
      </span>
      <span className={statusClass(pipelineKind)}>Pipeline: {pipelineLoading ? "Running" : "Idle"}</span>
      <span className={statusClass(autonomyKind)}>
        Autonomy: {autonomyInfo?.running ? "Running" : autonomyInfo?.enabled ? "Enabled" : "Disabled"}
      </span>
      {statusError ? <span className="badge badge-danger">{statusError}</span> : null}
    </section>
  );
}

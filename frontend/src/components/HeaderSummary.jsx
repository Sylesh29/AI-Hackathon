export default function HeaderSummary({
  autonomyInfo,
  impactScore,
  lastAutonomyRefreshAt,
  autonomyBeat,
  onClear,
  disableClear,
}) {
  const impactTone =
    impactScore === null ? "badge-neutral" : impactScore >= 80 ? "badge-success" : impactScore >= 60 ? "badge-warning" : "badge-danger";

  return (
    <header className="headerBlock">
      <div className="headerRow">
        <div>
          <h1>AutoPilotOps Console</h1>
          <p>Autonomous incident remediation with memory-driven learning and sponsor integrations.</p>
        </div>
        <button
          type="button"
          className="button buttonSecondary"
          onClick={onClear}
          disabled={disableClear}
          aria-label="Clear current run results"
        >
          Clear Results
        </button>
      </div>

      <section className="summaryGrid" aria-label="Summary metrics">
        <article className="card summaryCard">
          <p className="summaryLabel">Learning Score</p>
          <p className="summaryValue">{autonomyInfo ? `${autonomyInfo.learning_score}/100` : "-"}</p>
        </article>
        <article className="card summaryCard">
          <p className="summaryLabel">Impact Score</p>
          <p className={`summaryValue ${impactTone}`}>{impactScore === null ? "-" : `${impactScore}/100`}</p>
        </article>
        <article className="card summaryCard">
          <p className="summaryLabel">Autonomous Runs</p>
          <p className="summaryValue">{autonomyInfo ? autonomyInfo.total_runs : 0}</p>
        </article>
        <article className="card summaryCard">
          <p className="summaryLabel">Autonomy Feed</p>
          <p className="summaryValueSmall">
            <span className={`pulse ${autonomyBeat % 2 === 0 ? "pulseA" : "pulseB"}`} aria-hidden="true" />
            Auto refresh 12s
          </p>
          <p className="summaryHint">{lastAutonomyRefreshAt ? `Last sync ${lastAutonomyRefreshAt}` : "Waiting for sync"}</p>
        </article>
      </section>
    </header>
  );
}

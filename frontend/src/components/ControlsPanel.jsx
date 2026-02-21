export default function ControlsPanel({
  baseUrl,
  isProd,
  isBusy,
  selectedIncident,
  incidents,
  onBaseUrlChange,
  onIncidentChange,
  onRun,
  onSpeak,
  onExport,
  onAutonomyRun,
  pipelineLoading,
  speechLoading,
  autonomyLoading,
  hasPipelineResult,
  hasSummaryText,
}) {
  return (
    <section className="card controlsCard" aria-label="Controls panel">
      <div className="controlGroup">
        <label htmlFor="baseUrl">Backend URL</label>
        <input
          id="baseUrl"
          className="input"
          value={baseUrl}
          onChange={(event) => onBaseUrlChange(event.target.value)}
          placeholder="http://localhost:8000"
          readOnly={isProd}
          disabled={isBusy}
          aria-label="Backend URL"
        />
      </div>

      <div className="controlGroup">
        <span className="groupLabel">Incident Type</span>
        <div className="incidentButtons" role="group" aria-label="Incident selection">
          {incidents.map((incident) => (
            <button
              key={incident.id}
              className={`button ${selectedIncident === incident.id ? "buttonSelected" : "buttonSecondary"}`}
              onClick={() => onIncidentChange(incident.id)}
              type="button"
              disabled={isBusy}
            >
              {incident.label}
            </button>
          ))}
        </div>
      </div>

      <div className="actionRow">
        <button className="button buttonPrimary" onClick={onRun} type="button" disabled={isBusy}>
          {pipelineLoading ? "Running..." : "Run AutoPilotOps"}
        </button>
        <button
          className="button buttonSecondary"
          onClick={onSpeak}
          type="button"
          disabled={!hasSummaryText || speechLoading || pipelineLoading}
        >
          {speechLoading ? "Speaking..." : "Speak Summary"}
        </button>
        <button className="button buttonSecondary" onClick={onExport} type="button" disabled={!hasPipelineResult || isBusy}>
          Export Report JSON
        </button>
        <button className="button buttonSecondary" onClick={onAutonomyRun} type="button" disabled={isBusy || autonomyLoading}>
          {autonomyLoading ? "Autonomy..." : "Autonomy Tick"}
        </button>
      </div>
    </section>
  );
}

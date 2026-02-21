import { useState } from "react";

export default function SponsorToolsPanel({ autonomyInfo, autonomyRuns }) {
  const [open, setOpen] = useState(true);

  return (
    <article className="card spanFull">
      <button
        type="button"
        className="accordionToggle"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        aria-controls="sponsor-panel-content"
      >
        <span>Autonomy + Sponsor Tools</span>
        <span className="mono">{open ? "Hide" : "Show"}</span>
      </button>
      {open ? (
        <div id="sponsor-panel-content">
          <div className="kvRow">
            <span>Learning score</span>
            <span>{autonomyInfo ? `${autonomyInfo.learning_score}/100` : "-"}</span>
          </div>
          <div className="kvRow">
            <span>Memory hit rate</span>
            <span>{autonomyInfo ? `${autonomyInfo.memory_hit_rate_percent}%` : "-"}</span>
          </div>
          <div className="kvRow">
            <span>Integrations</span>
            <span className="mono">
              {autonomyInfo
                ? `Lightdash-${autonomyInfo.sponsor_integrations.lightdash}, Airia-${autonomyInfo.sponsor_integrations.airia}, Modulate-${autonomyInfo.sponsor_integrations.modulate}`
                : "-"}
            </span>
          </div>

          {autonomyRuns.length > 0 ? (
            <div className="runList" aria-label="Autonomous runs">
              {autonomyRuns.map((run, idx) => (
                <div className="runItem" key={`${run.request_id}-${idx}`}>
                  <span className="mono">{new Date(run.timestamp).toLocaleTimeString()}</span>
                  <span>{run.incident_type}</span>
                  <span>Impact: {run.impact_score ?? "-"}</span>
                  <span>Memory: {run.memory_used ? "yes" : "no"}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No autonomous runs yet.</p>
          )}
        </div>
      ) : null}
    </article>
  );
}

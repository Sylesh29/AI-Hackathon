export default function ReasoningPanel({ pipelineResult, loading }) {
  return (
    <article className="card">
      <div className="cardHeader">
        <h2>Agent Reasoning</h2>
      </div>
      {loading ? <div className="loadingBlock" /> : null}
      <div className="kvRow">
        <span>Anomaly</span>
        <span className="mono">{pipelineResult ? `${pipelineResult.incident_type}: ${pipelineResult.signature}` : "-"}</span>
      </div>
      <div className="kvRow">
        <span>Root Cause</span>
        <span>{pipelineResult?.reasoning || "-"}</span>
      </div>
      <div className="kvRow">
        <span>Confidence</span>
        <span>{pipelineResult ? (pipelineResult.memory_used ? "0.93" : "0.78") : "-"}</span>
      </div>
    </article>
  );
}

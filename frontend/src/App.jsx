import { useEffect, useMemo, useState } from "react";
import { fetchMemory, fetchStatus, runPipeline } from "./api.js";

const DEFAULT_BASE_URL = "http://localhost:8000";
const INCIDENTS = [
  { id: "db_timeout", label: "DB Timeout" },
  { id: "memory_leak", label: "Memory Leak" },
  { id: "rate_limit", label: "Rate Limit" },
];

function toEntries(metrics) {
  return Object.entries(metrics || {});
}

function formatNumber(value) {
  if (typeof value !== "number") return String(value);
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function computeImpactScore(before, after) {
  const deltas = [];
  for (const [key, beforeValue] of Object.entries(before || {})) {
    const afterValue = after?.[key];
    if (typeof beforeValue !== "number" || typeof afterValue !== "number" || beforeValue <= 0) {
      continue;
    }
    const improvement = (beforeValue - afterValue) / beforeValue;
    deltas.push(Math.max(-1, Math.min(1, improvement)));
  }
  if (deltas.length === 0) return null;
  const avg = deltas.reduce((sum, n) => sum + n, 0) / deltas.length;
  return Math.round(((avg + 1) / 2) * 100);
}

export default function App() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [selectedIncident, setSelectedIncident] = useState("db_timeout");
  const [pipelineResult, setPipelineResult] = useState(null);
  const [memoryEntries, setMemoryEntries] = useState([]);
  const [pipelineLoading, setPipelineLoading] = useState(false);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);
  const [pipelineError, setPipelineError] = useState("");
  const [memoryError, setMemoryError] = useState("");
  const [statusError, setStatusError] = useState("");
  const [statusInfo, setStatusInfo] = useState(null);

  const impactScore = useMemo(
    () => computeImpactScore(pipelineResult?.metrics_before, pipelineResult?.metrics_after),
    [pipelineResult]
  );

  async function loadMemory() {
    setMemoryLoading(true);
    setMemoryError("");
    try {
      const data = await fetchMemory(baseUrl);
      setMemoryEntries(data);
    } catch (err) {
      setMemoryEntries([]);
      setMemoryError(err instanceof Error ? err.message : "Failed to load memory.");
    } finally {
      setMemoryLoading(false);
    }
  }

  async function loadStatus() {
    setStatusLoading(true);
    setStatusError("");
    try {
      const data = await fetchStatus(baseUrl);
      setStatusInfo(data);
    } catch (err) {
      setStatusInfo(null);
      setStatusError(err instanceof Error ? err.message : "Failed to reach backend.");
    } finally {
      setStatusLoading(false);
    }
  }

  useEffect(() => {
    loadStatus();
    loadMemory();
  }, [baseUrl]);

  async function handleRun() {
    setPipelineLoading(true);
    setPipelineError("");
    try {
      const result = await runPipeline(baseUrl, selectedIncident);
      setPipelineResult(result);
      await loadMemory();
    } catch (err) {
      setPipelineError(err instanceof Error ? err.message : "Pipeline failed.");
    } finally {
      setPipelineLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="top">
        <h1>AutoPilotOps Console</h1>
        <p>Trigger incidents and inspect multi-agent remediation results.</p>
      </header>

      <section className="controls">
        <label htmlFor="baseUrl">Backend URL</label>
        <input
          id="baseUrl"
          value={baseUrl}
          onChange={(event) => setBaseUrl(event.target.value)}
          placeholder="http://localhost:8000"
        />
        <div className="incident-buttons">
          {INCIDENTS.map((incident) => (
            <button
              key={incident.id}
              className={incident.id === selectedIncident ? "active" : ""}
              onClick={() => setSelectedIncident(incident.id)}
              type="button"
            >
              {incident.label}
            </button>
          ))}
        </div>
        <button
          className="run-button"
          onClick={handleRun}
          type="button"
          disabled={pipelineLoading || statusLoading}
        >
          {pipelineLoading ? "Running..." : "Run AutoPilotOps"}
        </button>
        <div className="status-row">
          <span>
            Backend status:{" "}
            {statusLoading
              ? "Checking..."
              : statusInfo
              ? `${statusInfo.status} (uptime ${Math.round(statusInfo.uptime_seconds)}s)`
              : "Unavailable"}
          </span>
          {statusError && <span className="error-text">{statusError}</span>}
        </div>
        {pipelineError && <p className="error-text">Run failed: {pipelineError}</p>}
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Logs</h2>
          <div className="log-panel">
            {pipelineResult?.logs?.length ? (
              pipelineResult.logs.map((log, idx) => (
                <div key={`${log.agent}-${idx}`} className="log-row">
                  <span className="mono">{log.agent}</span>
                  <span>{log.message}</span>
                </div>
              ))
            ) : (
              <p className="muted">No logs yet.</p>
            )}
          </div>
        </article>

        <article className="panel">
          <h2>Agent Reasoning</h2>
          <div className="kv">
            <span>Anomaly</span>
            <span className="mono">
              {pipelineResult
                ? `${pipelineResult.incident_type}: ${pipelineResult.signature}`
                : "-"}
            </span>
          </div>
          <div className="kv">
            <span>Root Cause</span>
            <span>{pipelineResult?.reasoning || "-"}</span>
          </div>
          <div className="kv">
            <span>Confidence</span>
            <span>{pipelineResult ? (pipelineResult.memory_used ? "0.93" : "0.78") : "-"}</span>
          </div>
        </article>

        <article className="panel">
          <h2>Patch</h2>
          <div className="subhead">Plan</div>
          <ul className="plan">
            <li>Diagnose and select fix strategy</li>
            <li>Apply patch in sandbox</li>
            <li>Validate outcome and persist memory</li>
          </ul>
          <div className="subhead">Snippet</div>
          <pre>{pipelineResult?.patch || "Patch snippet will appear after run."}</pre>
        </article>

        <article className="panel">
          <h2>Impact</h2>
          <div className="metrics-grid">
            <div>
              <div className="subhead">Before</div>
              {toEntries(pipelineResult?.metrics_before).map(([key, value]) => (
                <div className="kv" key={`before-${key}`}>
                  <span>{key}</span>
                  <span>{formatNumber(value)}</span>
                </div>
              ))}
            </div>
            <div>
              <div className="subhead">After</div>
              {toEntries(pipelineResult?.metrics_after).map(([key, value]) => (
                <div className="kv" key={`after-${key}`}>
                  <span>{key}</span>
                  <span>{formatNumber(value)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="score">
            Impact score: <strong>{impactScore === null ? "-" : `${impactScore}/100`}</strong>
          </div>
        </article>

        <article className="panel full">
          <h2>Memory</h2>
          {memoryLoading && <p className="muted">Loading memory...</p>}
          {memoryError && <p className="error-text">Memory error: {memoryError}</p>}
          {!memoryLoading && !memoryError && memoryEntries.length === 0 && (
            <p className="muted">No learned patterns yet.</p>
          )}
          {!memoryLoading && !memoryError && memoryEntries.length > 0 && (
            <div className="memory-list">
              {memoryEntries.map((entry, idx) => (
                <div className="memory-row" key={`${entry.signature}-${idx}`}>
                  <div className="mono">{entry.signature}</div>
                  <div>{entry.fix}</div>
                  <div>Outcome: {entry.outcome}</div>
                  <div>Uses: {entry.uses}</div>
                  <div>Last used: {entry.last_used || "-"}</div>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>
    </div>
  );
}

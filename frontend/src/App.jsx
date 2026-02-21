import { useEffect, useMemo, useState } from "react";
import {
  fetchAutonomyRuns,
  fetchAutonomyStatus,
  fetchMemory,
  fetchStatus,
  runAutonomyOnce,
  runPipeline,
} from "./api.js";

const DEFAULT_BASE_URL = import.meta.env.PROD
  ? "/api"
  : import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
const IS_PROD = import.meta.env.PROD;
const INCIDENTS = [
  { id: "db_timeout", label: "DB Timeout" },
  { id: "memory_leak", label: "Memory Leak" },
  { id: "rate_limit", label: "Rate Limit" },
];
const ELEVENLABS_API_KEY = import.meta.env.VITE_ELEVENLABS_API_KEY;
const ELEVENLABS_VOICE_ID = import.meta.env.VITE_ELEVENLABS_VOICE_ID || "21m00Tcm4TlvDq8ikWAM";

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
  const [autonomyInfo, setAutonomyInfo] = useState(null);
  const [autonomyRuns, setAutonomyRuns] = useState([]);
  const [speechLoading, setSpeechLoading] = useState(false);
  const [autonomyLoading, setAutonomyLoading] = useState(false);
  const [speechError, setSpeechError] = useState("");
  const [toasts, setToasts] = useState([]);

  const isBusy = pipelineLoading || speechLoading;

  const impactScore = useMemo(
    () => computeImpactScore(pipelineResult?.metrics_before, pipelineResult?.metrics_after),
    [pipelineResult]
  );

  const selectedMemoryEntry = useMemo(() => {
    if (!pipelineResult?.signature) return null;
    return memoryEntries.find((entry) => entry.signature === pipelineResult.signature) || null;
  }, [memoryEntries, pipelineResult]);

  const summaryText = useMemo(() => {
    if (!pipelineResult) return "";
    const rootCause = pipelineResult.reasoning || "No root-cause reasoning available.";
    const fix = selectedMemoryEntry?.fix || pipelineResult.patch || "No fix generated.";
    return `Root cause: ${rootCause}. Fix: ${fix}`;
  }, [pipelineResult, selectedMemoryEntry]);

  function addToast(type, message) {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((current) => [...current, { id, type, message }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, 3500);
  }

  async function loadMemory() {
    setMemoryLoading(true);
    setMemoryError("");
    try {
      const data = await fetchMemory(baseUrl);
      setMemoryEntries(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load memory.";
      setMemoryEntries([]);
      setMemoryError(message);
      addToast("error", `Memory error: ${message}`);
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
      const message = err instanceof Error ? err.message : "Failed to reach backend.";
      setStatusInfo(null);
      setStatusError(message);
      addToast("error", `Status error: ${message}`);
    } finally {
      setStatusLoading(false);
    }
  }

  async function loadAutonomy() {
    try {
      const [status, runs] = await Promise.all([fetchAutonomyStatus(baseUrl), fetchAutonomyRuns(baseUrl, 5)]);
      setAutonomyInfo(status);
      setAutonomyRuns(runs.runs || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch autonomy status.";
      addToast("error", `Autonomy error: ${message}`);
    }
  }

  useEffect(() => {
    loadStatus();
    loadMemory();
    loadAutonomy();
  }, [baseUrl]);

  async function handleRun() {
    if (isBusy) return;
    setPipelineLoading(true);
    setPipelineError("");
    try {
      const result = await runPipeline(baseUrl, selectedIncident);
      setPipelineResult(result);
      await loadMemory();
      await loadAutonomy();
      addToast("success", "Incident pipeline completed.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Pipeline failed.";
      setPipelineError(message);
      addToast("error", `Run failed: ${message}`);
    } finally {
      setPipelineLoading(false);
    }
  }

  async function handleAutonomyRun() {
    if (isBusy || autonomyLoading) return;
    setAutonomyLoading(true);
    try {
      const result = await runAutonomyOnce(baseUrl);
      if (result.triggered && result.record?.incident_type) {
        addToast("success", `Autonomous run executed for ${result.record.incident_type}.`);
      } else {
        addToast("success", result.reason || "Autonomy checked, no incident triggered.");
      }
      await loadMemory();
      await loadAutonomy();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Autonomous run failed.";
      addToast("error", `Autonomy run failed: ${message}`);
    } finally {
      setAutonomyLoading(false);
    }
  }

  function speakWithBrowser(text) {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      throw new Error("Browser speech synthesis is unavailable.");
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }

  async function speakWithElevenLabs(text) {
    const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${ELEVENLABS_VOICE_ID}`, {
      method: "POST",
      headers: {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text, model_id: "eleven_multilingual_v2" }),
    });
    if (!res.ok) {
      throw new Error(`ElevenLabs request failed (${res.status}).`);
    }
    const audioBuffer = await res.arrayBuffer();
    const blob = new Blob([audioBuffer], { type: "audio/mpeg" });
    const audioUrl = URL.createObjectURL(blob);
    const audio = new Audio(audioUrl);
    audio.addEventListener("ended", () => URL.revokeObjectURL(audioUrl), { once: true });
    await audio.play();
  }

  async function handleSpeakSummary() {
    if (!summaryText || speechLoading || pipelineLoading) return;
    setSpeechLoading(true);
    setSpeechError("");
    try {
      if (ELEVENLABS_API_KEY) {
        try {
          await speakWithElevenLabs(summaryText);
        } catch {
          speakWithBrowser(summaryText);
        }
      } else {
        speakWithBrowser(summaryText);
      }
      addToast("success", "Speaking incident summary.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not play speech summary.";
      setSpeechError(message);
      addToast("error", `Speech error: ${message}`);
    } finally {
      setSpeechLoading(false);
    }
  }

  async function handleCopyPatch() {
    if (!pipelineResult?.patch || isBusy) return;
    try {
      if (!navigator?.clipboard?.writeText) {
        throw new Error("Clipboard API is unavailable in this browser.");
      }
      await navigator.clipboard.writeText(pipelineResult.patch);
      addToast("success", "Patch snippet copied.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to copy patch.";
      addToast("error", message);
    }
  }

  function handleExportReport() {
    if (!pipelineResult || isBusy) return;
    try {
      const report = {
        exported_at: new Date().toISOString(),
        backend_url: baseUrl,
        incident_type: pipelineResult.incident_type,
        signature: pipelineResult.signature,
        reasoning: pipelineResult.reasoning,
        patch: pipelineResult.patch,
        sandbox_result: pipelineResult.sandbox_result,
        metrics_before: pipelineResult.metrics_before,
        metrics_after: pipelineResult.metrics_after,
        impact_score: impactScore,
        logs: pipelineResult.logs,
        model_metrics: pipelineResult.model_metrics || null,
        memory_top: memoryEntries,
      };
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
      const href = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = href;
      anchor.download = `incident-report-${pipelineResult.incident_type}-${Date.now()}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(href);
      addToast("success", "Incident report exported.");
    } catch {
      addToast("error", "Failed to export incident report.");
    }
  }

  return (
    <div className="app">
      <header className="top">
        <h1>AutoPilotOps Console</h1>
        <p>Trigger incidents and inspect multi-agent remediation results.</p>
      </header>

      <section className="controls">
        <label htmlFor="baseUrl">Backend URL (VITE_BACKEND_URL)</label>
        <input
          id="baseUrl"
          value={baseUrl}
          onChange={(event) => {
            if (!IS_PROD && !isBusy) setBaseUrl(event.target.value);
          }}
          placeholder="http://localhost:8000"
          readOnly={IS_PROD}
          disabled={isBusy}
        />

        <div className="incident-buttons">
          {INCIDENTS.map((incident) => (
            <button
              key={incident.id}
              className={incident.id === selectedIncident ? "active" : ""}
              onClick={() => setSelectedIncident(incident.id)}
              type="button"
              disabled={isBusy}
            >
              {incident.label}
            </button>
          ))}
        </div>

        <div className="action-row">
          <button className="run-button" onClick={handleRun} type="button" disabled={isBusy || statusLoading}>
            {pipelineLoading ? "Running..." : "Run AutoPilotOps"}
          </button>
          <button
            className="speak-button"
            onClick={handleSpeakSummary}
            type="button"
            disabled={!pipelineResult || speechLoading || pipelineLoading}
          >
            {speechLoading ? "Speaking..." : "Speak Summary"}
          </button>
          <button
            className="secondary-button"
            onClick={handleExportReport}
            type="button"
            disabled={!pipelineResult || isBusy}
          >
            Export Report JSON
          </button>
          <button
            className="secondary-button"
            onClick={handleAutonomyRun}
            type="button"
            disabled={isBusy || autonomyLoading}
          >
            {autonomyLoading ? "Autonomy..." : "Autonomy Tick"}
          </button>
        </div>

        <div className="status-row">
          <span>
            Backend status:{" "}
            {statusLoading
              ? "Checking..."
              : statusInfo
              ? `${statusInfo.status} (uptime ${Math.round(statusInfo.uptime_seconds)}s)`
              : "Unavailable"}
          </span>
          <span>Pipeline: {pipelineLoading ? "Running" : "Idle"}</span>
          <span>
            Autonomy: {autonomyInfo?.running ? "Running" : autonomyInfo?.enabled ? "Enabled" : "Disabled"}
          </span>
          {statusError && <span className="error-text">{statusError}</span>}
        </div>

        {pipelineError && <p className="error-text">Run failed: {pipelineError}</p>}
        {speechError && <p className="error-text">Speech error: {speechError}</p>}
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Logs</h2>
          <div className="log-panel">
            {pipelineLoading && <p className="muted">Running pipeline...</p>}
            {!pipelineLoading && pipelineResult?.logs?.length ? (
              pipelineResult.logs.map((log, idx) => (
                <div key={`${log.agent}-${idx}`} className="log-row">
                  <span className="mono">{log.agent}</span>
                  <span>{log.message}</span>
                </div>
              ))
            ) : null}
            {!pipelineLoading && !pipelineResult?.logs?.length && <p className="muted">No logs yet.</p>}
          </div>
        </article>

        <article className="panel">
          <h2>Agent Reasoning</h2>
          <div className="kv">
            <span>Anomaly</span>
            <span className="mono">
              {pipelineResult ? `${pipelineResult.incident_type}: ${pipelineResult.signature}` : "-"}
            </span>
          </div>
          <div className="kv">
            <span>Root Cause</span>
            <span>{pipelineResult?.reasoning || (pipelineLoading ? "Analyzing..." : "-")}</span>
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
          <div className="panel-actions">
            <div className="subhead">Snippet</div>
            <button
              className="secondary-button"
              onClick={handleCopyPatch}
              type="button"
              disabled={!pipelineResult?.patch || isBusy}
            >
              Copy Patch
            </button>
          </div>
          <pre>{pipelineResult?.patch || (pipelineLoading ? "Generating patch..." : "Patch snippet will appear after run.")}</pre>
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
          <h2>Autonomy + Sponsor Tools</h2>
          <div className="kv">
            <span>Learning score</span>
            <span>{autonomyInfo ? `${autonomyInfo.learning_score}/100` : "-"}</span>
          </div>
          <div className="kv">
            <span>Memory hit rate</span>
            <span>{autonomyInfo ? `${autonomyInfo.memory_hit_rate_percent}%` : "-"}</span>
          </div>
          <div className="kv">
            <span>Integrations</span>
            <span className="mono">
              {autonomyInfo
                ? `Lightdash=${autonomyInfo.sponsor_integrations.lightdash}, Airia=${autonomyInfo.sponsor_integrations.airia}, Modulate=${autonomyInfo.sponsor_integrations.modulate}`
                : "-"}
            </span>
          </div>
          {autonomyRuns.length > 0 ? (
            <div className="memory-list">
              {autonomyRuns.map((run, idx) => (
                <div className="memory-row" key={`${run.request_id}-${idx}`}>
                  <div className="mono">{run.timestamp}</div>
                  <div>{run.incident_type}</div>
                  <div>Impact: {run.impact_score ?? "-"}</div>
                  <div>Memory used: {run.memory_used ? "yes" : "no"}</div>
                  <div>Lightdash: {run.sponsors?.lightdash || "-"}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No autonomous runs yet.</p>
          )}
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

      <div className="toast-stack">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}

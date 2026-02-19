import { useEffect, useMemo, useState } from "react";
import { fetchIncidents, fetchMemory, simulateIncident } from "./api.js";

const DEFAULT_BASE_URL = "http://localhost:8000";

const formatMetrics = (metrics) =>
  Object.entries(metrics || {})
    .map(([key, value]) => `${key}: ${value}`)
    .join("\n");

export default function App() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [incidents, setIncidents] = useState([]);
  const [selected, setSelected] = useState("");
  const [result, setResult] = useState(null);
  const [memory, setMemory] = useState([]);
  const [status, setStatus] = useState("Idle");

  const canSimulate = selected && status !== "Running";

  const summary = useMemo(() => {
    if (!result) return "Run a simulation to see results.";
    return `${result.incident_name} (${result.incident_id})`;
  }, [result]);

  useEffect(() => {
    fetchIncidents(baseUrl).then(setIncidents).catch(() => setIncidents([]));
    fetchMemory(baseUrl).then(setMemory).catch(() => setMemory([]));
  }, [baseUrl]);

  const runSimulation = async () => {
    if (!canSimulate) return;
    setStatus("Running");
    try {
      const data = await simulateIncident(baseUrl, selected);
      setResult(data);
      const updatedMemory = await fetchMemory(baseUrl);
      setMemory(updatedMemory);
      setStatus("Completed");
    } catch (err) {
      setStatus("Error");
    }
  };

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="badge">AutoPilotOps</p>
          <h1>Self-Improving AI DevOps Engineer</h1>
          <p className="lead">
            Simulate incidents, orchestrate multi-agent fixes, and watch memory
            strengthen over time.
          </p>
        </div>
        <div className="controls">
          <label>
            Backend URL
            <input
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              placeholder="http://localhost:8000"
            />
          </label>
          <label>
            Incident
            <select
              value={selected}
              onChange={(event) => setSelected(event.target.value)}
            >
              <option value="">Select incident</option>
              {incidents.map((incident) => (
                <option key={incident.id} value={incident.id}>
                  {incident.name}
                </option>
              ))}
            </select>
          </label>
          <button onClick={runSimulation} disabled={!canSimulate}>
            Run Incident Simulation
          </button>
          <p className="status">Status: {status}</p>
        </div>
      </header>

      <section className="grid">
        <div className="panel">
          <h2>Summary</h2>
          <p>{summary}</p>
          {result && (
            <div className="metrics-grid">
              <div>
                <h3>Before</h3>
                <pre>{formatMetrics(result.metrics_before)}</pre>
              </div>
              <div>
                <h3>After</h3>
                <pre>{formatMetrics(result.metrics_after)}</pre>
              </div>
            </div>
          )}
        </div>

        <div className="panel">
          <h2>Agent Logs</h2>
          <div className="log-list">
            {(result?.logs || []).map((log, index) => (
              <div key={`${log.agent}-${index}`} className="log-item">
                <span>{log.agent}</span>
                <p>{log.message}</p>
              </div>
            ))}
            {!result && <p className="muted">No logs yet.</p>}
          </div>
        </div>

        <div className="panel">
          <h2>Reasoning</h2>
          <p>{result?.reasoning || "Awaiting simulation."}</p>
          {result && (
            <div className="chips">
              <span>{result.memory_used ? "Memory hit" : "Fresh analysis"}</span>
              <span>{result.memory_written ? "Memory updated" : "No new memory"}</span>
            </div>
          )}
        </div>

        <div className="panel">
          <h2>Patch</h2>
          <pre>{result?.patch || "Patch will appear here."}</pre>
        </div>

        <div className="panel full">
          <h2>Memory</h2>
          <div className="memory-table">
            <div className="memory-row memory-head">
              <span>Signature</span>
              <span>Fix</span>
              <span>Outcome</span>
            </div>
            {memory.length === 0 && (
              <div className="memory-row">
                <span className="muted">No memory yet.</span>
              </div>
            )}
            {memory.map((entry, index) => (
              <div key={`${entry.signature}-${index}`} className="memory-row">
                <span>{entry.signature}</span>
                <span>{entry.fix}</span>
                <span>{entry.outcome}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

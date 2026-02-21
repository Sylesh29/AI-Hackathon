import { useEffect, useMemo, useState } from "react";
import {
  fetchAutonomyRuns,
  fetchAutonomyStatus,
  fetchMemory,
  fetchStatus,
  runAutonomyOnce,
  runPipeline,
  toApiError,
} from "./api.js";
import ControlsPanel from "./components/ControlsPanel.jsx";
import HeaderSummary from "./components/HeaderSummary.jsx";
import ImpactPanel from "./components/ImpactPanel.jsx";
import LogsPanel from "./components/LogsPanel.jsx";
import MemoryPanel from "./components/MemoryPanel.jsx";
import PatchPanel from "./components/PatchPanel.jsx";
import ReasoningPanel from "./components/ReasoningPanel.jsx";
import SponsorToolsPanel from "./components/SponsorToolsPanel.jsx";
import StatusBar from "./components/StatusBar.jsx";

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

function toMessage(error, fallback) {
  return toApiError(error, fallback).message;
}

function stampLogs(logs = []) {
  const base = Date.now();
  return logs.map((log, index) => ({
    ...log,
    timestamp: new Date(base + index * 600).toISOString(),
  }));
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
  const [lastAutonomyRefreshAt, setLastAutonomyRefreshAt] = useState(null);
  const [autonomyBeat, setAutonomyBeat] = useState(0);

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
    }, 3600);
  }

  async function loadMemory() {
    setMemoryLoading(true);
    setMemoryError("");
    try {
      const data = await fetchMemory(baseUrl);
      setMemoryEntries(data);
    } catch (error) {
      const message = toMessage(error, "Failed to load memory.");
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
    } catch (error) {
      const message = toMessage(error, "Failed to reach backend.");
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
      setLastAutonomyRefreshAt(new Date().toLocaleTimeString());
      setAutonomyBeat((value) => value + 1);
    } catch (error) {
      const message = toMessage(error, "Failed to fetch autonomy status.");
      addToast("error", `Autonomy error: ${message}`);
    }
  }

  useEffect(() => {
    loadStatus();
    loadMemory();
    loadAutonomy();
  }, [baseUrl]);

  useEffect(() => {
    const id = window.setInterval(() => {
      loadAutonomy();
    }, 12000);
    return () => window.clearInterval(id);
  }, [baseUrl]);

  async function handleRun() {
    if (isBusy) return;
    setPipelineLoading(true);
    setPipelineError("");
    try {
      const result = await runPipeline(baseUrl, selectedIncident);
      setPipelineResult({ ...result, logs: stampLogs(result.logs) });
      await loadMemory();
      await loadAutonomy();
      addToast("success", "Incident pipeline completed.");
    } catch (error) {
      const message = toMessage(error, "Pipeline failed.");
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
    } catch (error) {
      const message = toMessage(error, "Autonomous run failed.");
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
    } catch (error) {
      const message = toMessage(error, "Could not play speech summary.");
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
    } catch (error) {
      addToast("error", toMessage(error, "Failed to copy patch."));
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

  function handleClearResults() {
    setPipelineResult(null);
    setPipelineError("");
    setSpeechError("");
  }

  return (
    <div className="app">
      <HeaderSummary
        autonomyInfo={autonomyInfo}
        impactScore={impactScore}
        lastAutonomyRefreshAt={lastAutonomyRefreshAt}
        autonomyBeat={autonomyBeat}
        onClear={handleClearResults}
        disableClear={isBusy && !pipelineResult}
      />

      <ControlsPanel
        baseUrl={baseUrl}
        isProd={IS_PROD}
        isBusy={isBusy}
        selectedIncident={selectedIncident}
        incidents={INCIDENTS}
        onBaseUrlChange={(value) => {
          if (!IS_PROD && !isBusy) setBaseUrl(value);
        }}
        onIncidentChange={setSelectedIncident}
        onRun={handleRun}
        onSpeak={handleSpeakSummary}
        onExport={handleExportReport}
        onAutonomyRun={handleAutonomyRun}
        pipelineLoading={pipelineLoading}
        speechLoading={speechLoading}
        autonomyLoading={autonomyLoading}
        hasPipelineResult={Boolean(pipelineResult)}
        hasSummaryText={Boolean(summaryText)}
      />

      <StatusBar
        statusLoading={statusLoading}
        statusInfo={statusInfo}
        pipelineLoading={pipelineLoading}
        autonomyInfo={autonomyInfo}
        statusError={statusError}
      />

      {pipelineError ? <p className="errorText">Run failed: {pipelineError}</p> : null}
      {speechError ? <p className="errorText">Speech error: {speechError}</p> : null}

      <section className="dashboardGrid">
        <LogsPanel logs={pipelineResult?.logs || []} loading={pipelineLoading} />
        <ReasoningPanel pipelineResult={pipelineResult} loading={pipelineLoading} />
        <PatchPanel
          patch={pipelineResult?.patch}
          loading={pipelineLoading}
          onCopy={handleCopyPatch}
          disabled={!pipelineResult?.patch || isBusy}
        />
        <ImpactPanel
          before={pipelineResult?.metrics_before}
          after={pipelineResult?.metrics_after}
          impactScore={impactScore}
        />
        <SponsorToolsPanel autonomyInfo={autonomyInfo} autonomyRuns={autonomyRuns} />
        <MemoryPanel entries={memoryEntries} loading={memoryLoading} error={memoryError} />
      </section>

      <div className="toastStack" aria-live="polite" aria-atomic="true">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}

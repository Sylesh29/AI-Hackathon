const API_KEY = import.meta.env.VITE_API_KEY;
const DEFAULT_BASE_URL = import.meta.env.PROD
  ? "/api"
  : import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

async function requestJson(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }
  const res = await fetch(url, { ...options, headers });
  const requestId = res.headers.get("x-request-id");
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (data?.error?.message) {
        detail = data.error.message;
      } else if (data?.detail) {
        detail = data.detail;
      }
      if (data?.request_id || requestId) {
        detail = `${detail} (request_id: ${data?.request_id || requestId})`;
      }
    } catch {
      // Ignore parsing error and keep the default HTTP status detail.
    }
    throw new Error(detail);
  }
  const data = await res.json();
  if (data && typeof data === "object" && "data" in data) {
    return data.data;
  }
  return data;
}

export function fetchStatus(baseUrl) {
  return requestJson(`${baseUrl || DEFAULT_BASE_URL}/status`);
}

export async function runPipeline(baseUrl, incidentType) {
  return requestJson(`${baseUrl || DEFAULT_BASE_URL}/run_pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ incident_type: incidentType }),
  });
}

export async function fetchMemory(baseUrl) {
  const data = await requestJson(`${baseUrl || DEFAULT_BASE_URL}/memory`);
  return data.entries || [];
}

export function fetchAutonomyStatus(baseUrl) {
  return requestJson(`${baseUrl || DEFAULT_BASE_URL}/autonomy/status`);
}

export function fetchAutonomyRuns(baseUrl, limit = 5) {
  return requestJson(`${baseUrl || DEFAULT_BASE_URL}/autonomy/runs?limit=${limit}`);
}

export function runAutonomyOnce(baseUrl) {
  return requestJson(`${baseUrl || DEFAULT_BASE_URL}/autonomy/run_once`, {
    method: "POST",
  });
}

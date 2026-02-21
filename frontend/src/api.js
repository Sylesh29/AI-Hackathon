const API_KEY = import.meta.env.VITE_API_KEY;
const DEFAULT_BASE_URL = import.meta.env.PROD
  ? "/api"
  : import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 12000;

export class ApiError extends Error {
  constructor({ message, code = "unknown_error", status = 0, requestId = null, cause = null }) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.requestId = requestId;
    this.cause = cause;
  }
}

export function toApiError(error, fallbackMessage = "Request failed.") {
  if (error instanceof ApiError) {
    return error;
  }
  if (error?.name === "AbortError") {
    return new ApiError({
      message: "Request timed out. Please try again.",
      code: "request_timeout",
      status: 408,
      cause: error,
    });
  }
  return new ApiError({
    message: error instanceof Error ? error.message : fallbackMessage,
    code: "request_failed",
    cause: error,
  });
}

async function requestJson(url, options = {}, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  const headers = new Headers(options.headers || {});
  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }
  let res;
  try {
    res = await fetch(url, { ...options, headers, signal: controller.signal });
  } catch (error) {
    throw toApiError(error);
  } finally {
    window.clearTimeout(timeoutId);
  }

  const requestId = res.headers.get("x-request-id");
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    let code = "http_error";
    try {
      const data = await res.json();
      if (data?.error?.message) {
        message = data.error.message;
      } else if (data?.detail) {
        message = data.detail;
      }
      code = data?.error?.code || code;
      if (data?.request_id || requestId) {
        message = `${message} (request_id: ${data?.request_id || requestId})`;
      }
    } catch {
      // Ignore parsing error and keep the default HTTP status detail.
    }
    throw new ApiError({
      message,
      code,
      status: res.status,
      requestId,
    });
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

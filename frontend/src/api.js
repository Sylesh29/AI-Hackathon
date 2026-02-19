async function requestJson(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = data.detail;
    } catch {
      // Ignore parsing error and keep the default HTTP status detail.
    }
    throw new Error(detail);
  }
  return res.json();
}

export function fetchStatus(baseUrl) {
  return requestJson(`${baseUrl}/status`);
}

export async function runPipeline(baseUrl, incidentType) {
  return requestJson(`${baseUrl}/run_pipeline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ incident_type: incidentType }),
  });
}

export async function fetchMemory(baseUrl) {
  const data = await requestJson(`${baseUrl}/memory`);
  return data.entries || [];
}

export async function fetchIncidents(baseUrl) {
  const res = await fetch(`${baseUrl}/incidents`);
  if (!res.ok) {
    throw new Error("Failed to fetch incidents");
  }
  return res.json();
}

export async function simulateIncident(baseUrl, incidentId) {
  const res = await fetch(`${baseUrl}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ incident_id: incidentId }),
  });
  if (!res.ok) {
    throw new Error("Simulation failed");
  }
  return res.json();
}

export async function fetchMemory(baseUrl) {
  const res = await fetch(`${baseUrl}/memory`);
  if (!res.ok) {
    throw new Error("Failed to fetch memory");
  }
  const data = await res.json();
  return data.entries || [];
}

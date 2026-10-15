// The frontend only ever calls relative /api URLs. In Docker, nginx proxies them to the
// backend; in Kubernetes, the Ingress routes /api to the backend Service.
async function call(path, { method = "GET", body } = {}) {
  const res = await fetch(`/api${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((e) => `${e.loc.at(-1)}: ${e.msg}`).join("; ")
      : detail;
    throw new Error(message || `HTTP ${res.status}`);
  }
  return data;
}

const query = (params) => {
  const clean = Object.entries(params).filter(([, v]) => v !== "" && v !== false && v != null);
  return clean.length ? `?${new URLSearchParams(clean)}` : "";
};

export const listItems = (filters) => call(`/items${query(filters)}`);
export const getSummary = () => call("/summary");
export const getCategories = () => call("/categories");
export const createItem = (item) => call("/items", { method: "POST", body: item });
export const updateItem = (id, item) => call(`/items/${id}`, { method: "PUT", body: item });
export const deleteItem = (id) => call(`/items/${id}`, { method: "DELETE" });
export const moveStock = (id, change, reason) =>
  call(`/items/${id}/movements`, { method: "POST", body: { change, reason } });
export const getMovements = (id) => call(`/items/${id}/movements`);

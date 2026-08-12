const BASE_URL = "http://localhost:8000";
const TOKEN_KEY = "glide_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response body wasn't JSON; fall back to statusText
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  register: (payload) => request("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/api/auth/me"),

  getEarnings: (workerId) => request(`/api/earnings/${workerId}`),
  addEarnings: (payload) => request("/api/earnings", { method: "POST", body: JSON.stringify(payload) }),

  getForecast: (workerId) => request(`/api/forecast/${workerId}`),
  getExplanation: (workerId) => request(`/api/forecast/explain/${workerId}`),

  getBuffer: (workerId) => request(`/api/buffer/${workerId}`),
  deposit: (amount) => request("/api/buffer/deposit", { method: "POST", body: JSON.stringify({ amount }) }),
  withdraw: (amount) => request("/api/buffer/withdraw", { method: "POST", body: JSON.stringify({ amount }) }),

  getAlerts: (workerId) => request(`/api/alerts/${workerId}`),
  getDashboard: (workerId) => request(`/api/dashboard/${workerId}`),
};

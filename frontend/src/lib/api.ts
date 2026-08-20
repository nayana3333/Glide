// Set VITE_API_URL in production (e.g. Vercel env vars) to point at the
// deployed backend; falls back to the local dev server otherwise.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "glide_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// --- Types mirroring backend/app/schemas/*.py -----------------------------

export type Archetype = "full_time_driver" | "part_time_delivery" | "multi_platform";
export type Platform = "Ola" | "Uber" | "Swiggy" | "Zomato" | "UrbanCompany";
export type DipLevel = "GREEN" | "AMBER" | "RED";

export interface RegisterRequest {
  name: string;
  phone: string;
  password: string;
  archetype: Archetype;
  platform: Platform;
  demo_worker_id?: number | null;
}

export interface LoginRequest {
  phone: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  name: string;
  phone: string;
  archetype: Archetype;
  platform: Platform;
}

export interface EarningsCreate {
  week_start: string;
  platform: Platform;
  hours_worked: number;
  trips_completed: number;
  gross_earnings: number;
  fuel_cost: number;
}

export interface EarningsResponse {
  id: number;
  week_start: string;
  week_index: number;
  platform: Platform;
  hours_worked: number;
  trips_completed: number;
  gross_earnings: number;
  fuel_cost: number;
  net_earnings: number;
}

export interface ForecastWeek {
  week_start: string;
  yhat: number;
  yhat_lower: number | null;
  yhat_upper: number | null;
  dip_level: DipLevel;
  deficit_ratio: number;
}

export interface ForecastResponse {
  worker_id: number;
  model_used: string;
  rolling_avg: number;
  forecast: ForecastWeek[];
}

export interface ExplainResponse {
  worker_id: number;
  predicted: number;
  rolling_avg_4wk: number;
  deficit_ratio: number;
  contributions: Record<string, number>;
}

export interface BufferTransactionResponse {
  id: number;
  week_start: string;
  kind: "auto_save" | "auto_release" | "manual_deposit" | "manual_withdraw";
  amount: number;
  balance_after: number;
}

export interface BufferStateResponse {
  balance: number;
  transactions: BufferTransactionResponse[];
}

export interface AlertResponse {
  id: number;
  week_start: string;
  level: DipLevel;
  predicted_income: number;
  rolling_avg: number;
  message: string;
}

export interface DashboardResponse {
  worker_id: number;
  recent_earnings: EarningsResponse[];
  next_week_forecast: ForecastWeek | null;
  buffer_balance: number;
  latest_alert_message: string | null;
}

// --- Request helper ---------------------------------------------------------

class ApiError extends Error {}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
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
    throw new ApiError(detail);
  }
  if (res.status === 204) return null as T;
  return res.json();
}

export const api = {
  register: (payload: RegisterRequest) =>
    request<TokenResponse>("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload: LoginRequest) =>
    request<TokenResponse>("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request<UserResponse>("/api/auth/me"),

  getEarnings: (workerId: number) => request<EarningsResponse[]>(`/api/earnings/${workerId}`),
  addEarnings: (payload: EarningsCreate) =>
    request<EarningsResponse>("/api/earnings", { method: "POST", body: JSON.stringify(payload) }),

  getForecast: (workerId: number) => request<ForecastResponse>(`/api/forecast/${workerId}`),
  getExplanation: (workerId: number) => request<ExplainResponse>(`/api/forecast/explain/${workerId}`),

  getBuffer: (workerId: number) => request<BufferStateResponse>(`/api/buffer/${workerId}`),
  deposit: (amount: number) =>
    request<BufferTransactionResponse>("/api/buffer/deposit", {
      method: "POST",
      body: JSON.stringify({ amount }),
    }),
  withdraw: (amount: number) =>
    request<BufferTransactionResponse>("/api/buffer/withdraw", {
      method: "POST",
      body: JSON.stringify({ amount }),
    }),

  getAlerts: (workerId: number) => request<AlertResponse[]>(`/api/alerts/${workerId}`),
  getDashboard: (workerId: number) => request<DashboardResponse>(`/api/dashboard/${workerId}`),
};

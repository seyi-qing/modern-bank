/**
 * API client for ModernBank backend.
 * Transfers use Banking Core v2.1 (/banking/v2/transfer) with Idempotency-Key.
 */

import axios, { AxiosError } from "axios";
import {
  isDemoMode,
  demoUser,
  demoAdmin,
  demoDashboard,
  demoAccounts,
  demoTransactions,
  demoCards,
  demoInsights,
  demoGoals,
  demoNotifications,
  demoAdminStats,
  demoAdminUsers,
  exitDemoMode,
} from "./demo";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function getApiBase() {
  return API_BASE;
}

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 20000,
});

const TOKEN_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

export function readToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return (
      sessionStorage.getItem(TOKEN_KEY) ||
      localStorage.getItem(TOKEN_KEY) ||
      null
    );
  } catch {
    return null;
  }
}

export function setAuthToken(token: string | null) {
  if (typeof window === "undefined") return;
  try {
    if (token) {
      sessionStorage.setItem(TOKEN_KEY, token);
      localStorage.setItem(TOKEN_KEY, token);
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
      sessionStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(TOKEN_KEY);
      delete api.defaults.headers.common["Authorization"];
    }
  } catch {
    /* private mode */
  }
}

export function hydrateAuthFromStorage() {
  const token = readToken();
  if (token && token !== "demo-token") {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    return token;
  }
  return null;
}

if (typeof window !== "undefined") {
  hydrateAuthFromStorage();
}

api.interceptors.request.use((config) => {
  const token = readToken();
  if (token && token !== "demo-token") {
    const headers = config.headers as any;
    if (headers && typeof headers.set === "function") {
      headers.set("Authorization", `Bearer ${token}`);
    } else {
      config.headers = {
        ...(config.headers as any),
        Authorization: `Bearer ${token}`,
      } as any;
    }
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (
      error.response?.status === 401 &&
      typeof window !== "undefined" &&
      !isDemoMode()
    ) {
      const path = window.location.pathname;
      if (!path.includes("/login") && !path.includes("/register")) {
        setAuthToken(null);
        try {
          localStorage.removeItem(REFRESH_KEY);
          sessionStorage.removeItem(REFRESH_KEY);
        } catch {
          /* */
        }
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

function networkMessage(err: any): string {
  if (!err?.response) {
    return `Cannot reach API at ${API_BASE}. Deploy the FastAPI backend and set NEXT_PUBLIC_API_URL, or use Offline demo.`;
  }
  const d = err.response.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x: any) => x.msg || JSON.stringify(x)).join(", ");
  return err.message || "Request failed";
}

export function newIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `mb-${Date.now()}-${Math.random().toString(36).slice(2, 12)}-${Math.random().toString(36).slice(2, 12)}`;
}

export async function login(email: string, password: string) {
  try {
    exitDemoMode();
    const { data } = await api.post("/auth/login/json", { email, password });
    if (!data?.access_token) {
      throw new Error("Login response missing access_token");
    }
    setAuthToken(data.access_token);
    try {
      localStorage.setItem(REFRESH_KEY, data.refresh_token);
      sessionStorage.setItem(REFRESH_KEY, data.refresh_token);
    } catch {
      /* */
    }
    return data;
  } catch (err: any) {
    const e = new Error(networkMessage(err)) as any;
    e.response = err.response;
    e.isNetwork = !err.response;
    throw e;
  }
}

export async function register(payload: {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
}) {
  const { data } = await api.post("/auth/register", payload);
  return data;
}

export async function getMe() {
  if (isDemoMode()) {
    const email = localStorage.getItem("demo_role") === "admin" ? demoAdmin.email : demoUser.email;
    return email.startsWith("admin") ? demoAdmin : demoUser;
  }
  hydrateAuthFromStorage();
  const { data } = await api.get("/auth/me");
  return data;
}

export function logout() {
  exitDemoMode();
  setAuthToken(null);
  try {
    localStorage.removeItem(REFRESH_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem("demo_role");
    sessionStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* */
  }
  if (typeof window !== "undefined") {
    window.location.replace("/login");
  }
}

export async function getDashboard() {
  if (isDemoMode()) return demoDashboard;
  hydrateAuthFromStorage();
  const { data } = await api.get("/banking/dashboard");
  return data;
}

export async function getAccounts() {
  if (isDemoMode()) return demoAccounts;
  hydrateAuthFromStorage();
  const { data } = await api.get("/banking/accounts");
  return data;
}

export async function transfer(payload: {
  from_account_id: number;
  to_account_number: string;
  amount: number;
  description?: string;
  currency?: string;
  idempotency_key?: string;
}) {
  if (isDemoMode()) {
    const flagged = payload.amount >= 2000;
    return {
      id: Date.now(),
      amount: payload.amount,
      reference: `TXN-DEMO${Date.now().toString(36).toUpperCase()}`,
      is_flagged: flagged,
      fraud_score: flagged ? 0.71 : 0.08,
      status: flagged ? "flagged" : "completed",
      description: payload.description,
    };
  }
  hydrateAuthFromStorage();
  const idempotencyKey = payload.idempotency_key || newIdempotencyKey();
  const body = {
    from_account_id: payload.from_account_id,
    to_account_number: payload.to_account_number,
    amount: payload.amount,
    currency: (payload.currency || "USD").toUpperCase(),
    description: payload.description,
    idempotency_key: idempotencyKey,
  };
  const { data } = await api.post("/banking/v2/transfer", body, {
    headers: { "Idempotency-Key": idempotencyKey },
  });
  return data;
}

export async function getTransactions(accountId?: number, limit = 50) {
  if (isDemoMode()) return demoTransactions;
  hydrateAuthFromStorage();
  const params: any = { limit };
  if (accountId) params.account_id = accountId;
  const { data } = await api.get("/banking/transactions", { params });
  return data;
}

export async function getInsights() {
  if (isDemoMode()) return demoInsights;
  hydrateAuthFromStorage();
  const { data } = await api.get("/banking/insights");
  return data;
}

export async function getGoals() {
  if (isDemoMode()) return demoGoals;
  hydrateAuthFromStorage();
  const { data } = await api.get("/banking/goals");
  return data;
}

export async function createGoal(payload: {
  name: string;
  target_amount: number;
  deadline?: string;
}) {
  if (isDemoMode()) {
    return { id: Date.now(), current_amount: 0, ...payload };
  }
  hydrateAuthFromStorage();
  const { data } = await api.post("/banking/goals", payload);
  return data;
}

export async function getAdminStats() {
  if (isDemoMode()) return demoAdminStats;
  hydrateAuthFromStorage();
  const { data } = await api.get("/admin/stats");
  return data;
}

export async function getAdminUsers() {
  if (isDemoMode()) return demoAdminUsers;
  hydrateAuthFromStorage();
  const { data } = await api.get("/admin/users");
  return data;
}

export async function getFlaggedTransactions() {
  if (isDemoMode()) return demoTransactions.filter((t) => t.is_flagged);
  hydrateAuthFromStorage();
  const { data } = await api.get("/admin/transactions/flagged");
  return data;
}

export async function getAdminAllTransactions(limit = 100) {
  if (isDemoMode()) return demoTransactions;
  hydrateAuthFromStorage();
  const { data } = await api.get("/admin/transactions", { params: { limit } });
  return data;
}

export async function reviewFlaggedTransaction(
  transactionId: number,
  action: "approve" | "reject",
  reason: string
) {
  if (isDemoMode()) {
    return {
      id: transactionId,
      status: action === "approve" ? "completed" : "failed",
      is_flagged: action === "reject",
    };
  }
  hydrateAuthFromStorage();
  const { data } = await api.post(`/admin/core/transactions/${transactionId}/review`, {
    action,
    reason,
  });
  return data;
}

export async function getReconciliation() {
  if (isDemoMode()) {
    return {
      accounts_checked: 3,
      accounts_balanced: 3,
      accounts_out_of_balance: 0,
      ok: true,
      results: [],
    };
  }
  hydrateAuthFromStorage();
  const { data } = await api.get("/admin/core/reconciliation");
  return data;
}

export async function getCards() {
  if (isDemoMode()) return demoCards;
  hydrateAuthFromStorage();
  const { data } = await api.get("/cards");
  return data;
}

export async function createCard(payload: {
  account_id: number;
  card_type?: "virtual" | "physical";
  label?: string;
  spending_limit?: number;
}) {
  if (isDemoMode()) {
    const last4 = String(Math.floor(1000 + Math.random() * 9000));
    return {
      id: Date.now(),
      card_number_masked: `•••• •••• •••• ${last4}`,
      last_four: last4,
      card_type: payload.card_type || "virtual",
      status: "active",
      expiry_month: 12,
      expiry_year: 2029,
      spending_limit: payload.spending_limit ?? 1500,
      label: payload.label || "Virtual",
    };
  }
  hydrateAuthFromStorage();
  const { data } = await api.post("/cards", payload);
  return data;
}

export async function freezeCard(cardId: number) {
  if (isDemoMode()) return { id: cardId, status: "frozen" };
  hydrateAuthFromStorage();
  const { data } = await api.post(`/cards/${cardId}/freeze`);
  return data;
}

export async function unfreezeCard(cardId: number) {
  if (isDemoMode()) return { id: cardId, status: "active" };
  hydrateAuthFromStorage();
  const { data } = await api.post(`/cards/${cardId}/unfreeze`);
  return data;
}

export async function getNotifications(limit = 30) {
  if (isDemoMode()) return demoNotifications;
  hydrateAuthFromStorage();
  const { data } = await api.get("/notifications", { params: { limit } });
  return data;
}

export async function markNotificationsRead(ids?: number[]) {
  if (isDemoMode()) return { ok: true };
  hydrateAuthFromStorage();
  const { data } = await api.post("/notifications/read", ids ?? null);
  return data;
}

export function getWsUrl(): string {
  return `${API_BASE.replace(/^http/, "ws")}/notifications/ws`;
}

export async function getPaymentConfig() {
  if (isDemoMode()) return { enabled: false };
  hydrateAuthFromStorage();
  const { data } = await api.get("/payments/config");
  return data;
}

export async function createDepositIntent(payload: {
  account_id: number;
  amount: number;
  currency?: string;
}) {
  hydrateAuthFromStorage();
  const { data } = await api.post("/payments/deposit-intent", payload);
  return data;
}

export async function getBaasDashboard() {
  if (isDemoMode()) {
    return {
      deposit_accounts: 2,
      total_available: 12500,
      wallets: 1,
      credit_accounts: 1,
    };
  }
  hydrateAuthFromStorage();
  const { data } = await api.get("/baas/dashboard");
  return data;
}

export async function listBaasAccounts() {
  if (isDemoMode()) {
    return [
      {
        id: 1,
        name: "Alex Rivera Checking",
        deposit_product: "checking",
        account_number: "1000000002",
        available: 10000,
        balance: 10000,
      },
      {
        id: 2,
        name: "Operating Wallet (FBO)",
        deposit_product: "wallet",
        account_number: "9000000001",
        available: 2500,
        balance: 2500,
      },
    ];
  }
  hydrateAuthFromStorage();
  const { data } = await api.get("/baas/accounts");
  return data;
}

export async function openBaasAccount(payload: any) {
  hydrateAuthFromStorage();
  const { data } = await api.post("/baas/accounts", payload);
  return data;
}

export async function createBaasPayment(payload: any) {
  hydrateAuthFromStorage();
  const { data } = await api.post("/baas/payments", payload);
  return data;
}

export async function listBaasPayments(limit = 50) {
  if (isDemoMode()) return [];
  hydrateAuthFromStorage();
  const { data } = await api.get("/baas/payments", { params: { limit } });
  return data;
}

export async function listBaasCards() {
  if (isDemoMode()) return [];
  hydrateAuthFromStorage();
  const { data } = await api.get("/baas/cards");
  return data;
}

export async function issueBaasCard(payload: any) {
  hydrateAuthFromStorage();
  const { data } = await api.post("/baas/cards", payload);
  return data;
}

export async function toggleBaasCardFreeze(cardId: number) {
  hydrateAuthFromStorage();
  const { data } = await api.post(`/baas/cards/${cardId}/toggle-freeze`);
  return data;
}

export async function listCreditAccounts() {
  if (isDemoMode()) return [];
  hydrateAuthFromStorage();
  const { data } = await api.get("/baas/credit-accounts");
  return data;
}

export async function openCreditAccount(payload: any) {
  hydrateAuthFromStorage();
  const { data } = await api.post("/baas/credit-accounts", payload);
  return data;
}

// re-export for pages that import isDemoMode from api by mistake
export { isDemoMode };

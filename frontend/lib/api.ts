/**
 * API client for ModernBank backend.
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

function readToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setAuthToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem("access_token", token);
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    localStorage.removeItem("access_token");
    delete api.defaults.headers.common["Authorization"];
  }
}

api.interceptors.request.use((config) => {
  const token = readToken();
  if (token && token !== "demo-token") {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
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
      // Never silent-bounce during auth pages — show the error instead
      if (!path.includes("/login") && !path.includes("/register")) {
        setAuthToken(null);
        localStorage.removeItem("refresh_token");
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

export async function login(email: string, password: string) {
  try {
    const { data } = await api.post("/auth/login/json", { email, password });
    setAuthToken(data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    exitDemoMode();
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
  const { data } = await api.get("/auth/me");
  return data;
}

export function logout() {
  exitDemoMode();
  setAuthToken(null);
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("demo_role");
  if (typeof window !== "undefined") window.location.href = "/login";
}

export async function getDashboard() {
  if (isDemoMode()) return demoDashboard;
  const { data } = await api.get("/banking/dashboard");
  return data;
}

export async function getAccounts() {
  if (isDemoMode()) return demoAccounts;
  const { data } = await api.get("/banking/accounts");
  return data;
}

export async function transfer(payload: {
  from_account_id: number;
  to_account_number: string;
  amount: number;
  description?: string;
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
  const { data } = await api.post("/banking/transfer", payload);
  return data;
}

export async function getTransactions(accountId?: number, limit = 50) {
  if (isDemoMode()) return demoTransactions;
  const params: any = { limit };
  if (accountId) params.account_id = accountId;
  const { data } = await api.get("/banking/transactions", { params });
  return data;
}

export async function getInsights() {
  if (isDemoMode()) return demoInsights;
  const { data } = await api.get("/banking/insights");
  return data;
}

export async function getGoals() {
  if (isDemoMode()) return demoGoals;
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
  const { data } = await api.post("/banking/goals", payload);
  return data;
}

export async function getAdminStats() {
  if (isDemoMode()) return demoAdminStats;
  const { data } = await api.get("/admin/stats");
  return data;
}

export async function getAdminUsers() {
  if (isDemoMode()) return demoAdminUsers;
  const { data } = await api.get("/admin/users");
  return data;
}

export async function getFlaggedTransactions() {
  if (isDemoMode()) return demoTransactions.filter((t) => t.is_flagged);
  const { data } = await api.get("/admin/transactions/flagged");
  return data;
}

export async function getCards() {
  if (isDemoMode()) return demoCards;
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
  const { data } = await api.post("/cards", payload);
  return data;
}

export async function freezeCard(cardId: number) {
  if (isDemoMode()) return { id: cardId, status: "frozen" };
  const { data } = await api.post(`/cards/${cardId}/freeze`);
  return data;
}

export async function unfreezeCard(cardId: number) {
  if (isDemoMode()) return { id: cardId, status: "active" };
  const { data } = await api.post(`/cards/${cardId}/unfreeze`);
  return data;
}

export async function getNotifications(limit = 30) {
  if (isDemoMode()) return demoNotifications;
  const { data } = await api.get("/notifications", { params: { limit } });
  return data;
}

export async function markNotificationsRead(ids?: number[]) {
  if (isDemoMode()) return { ok: true };
  const { data } = await api.post("/notifications/read", ids ?? null);
  return data;
}

export function getWsUrl(): string {
  return `${API_BASE.replace(/^http/, "ws")}/notifications/ws`;
}

export async function getPaymentConfig() {
  if (isDemoMode()) return { enabled: false };
  const { data } = await api.get("/payments/config");
  return data;
}

export async function createDepositIntent(payload: {
  account_id: number;
  amount: number;
  currency?: string;
}) {
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
  const { data } = await api.get("/baas/accounts");
  return data;
}

export async function openBaasAccount(payload: any) {
  const { data } = await api.post("/baas/accounts", payload);
  return data;
}

export async function createBaasPayment(payload: any) {
  const { data } = await api.post("/baas/payments", payload);
  return data;
}

export async function listBaasPayments(limit = 50) {
  if (isDemoMode()) return [];
  const { data } = await api.get("/baas/payments", { params: { limit } });
  return data;
}

export async function listBaasCards() {
  if (isDemoMode()) return [];
  const { data } = await api.get("/baas/cards");
  return data;
}

export async function issueBaasCard(payload: any) {
  const { data } = await api.post("/baas/cards", payload);
  return data;
}

export async function toggleBaasCardFreeze(cardId: number) {
  const { data } = await api.post(`/baas/cards/${cardId}/toggle-freeze`);
  return data;
}

export async function listCreditAccounts() {
  if (isDemoMode()) return [];
  const { data } = await api.get("/baas/credit-accounts");
  return data;
}

export async function openCreditAccount(payload: any) {
  const { data } = await api.post("/baas/credit-accounts", payload);
  return data;
}

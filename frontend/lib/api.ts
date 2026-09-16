/**
 * API client for ModernBank backend.
 */

import axios, { AxiosError } from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      if (!window.location.pathname.includes("/login") && !window.location.pathname.includes("/register")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export async function login(email: string, password: string) {
  const { data } = await api.post("/auth/login/json", { email, password });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  return data;
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
  const { data } = await api.get("/auth/me");
  return data;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  if (typeof window !== "undefined") window.location.href = "/login";
}

export async function getDashboard() {
  const { data } = await api.get("/banking/dashboard");
  return data;
}

export async function getAccounts() {
  const { data } = await api.get("/banking/accounts");
  return data;
}

export async function transfer(payload: {
  from_account_id: number;
  to_account_number: string;
  amount: number;
  description?: string;
}) {
  const { data } = await api.post("/banking/transfer", payload);
  return data;
}

export async function getTransactions(accountId?: number, limit = 50) {
  const params: any = { limit };
  if (accountId) params.account_id = accountId;
  const { data } = await api.get("/banking/transactions", { params });
  return data;
}

export async function getInsights() {
  const { data } = await api.get("/banking/insights");
  return data;
}

export async function getGoals() {
  const { data } = await api.get("/banking/goals");
  return data;
}

export async function createGoal(payload: { name: string; target_amount: number; deadline?: string }) {
  const { data } = await api.post("/banking/goals", payload);
  return data;
}

export async function getAdminStats() {
  const { data } = await api.get("/admin/stats");
  return data;
}

export async function getAdminUsers() {
  const { data } = await api.get("/admin/users");
  return data;
}

export async function getFlaggedTransactions() {
  const { data } = await api.get("/admin/transactions/flagged");
  return data;
}

export async function getCards() {
  const { data } = await api.get("/cards");
  return data;
}

export async function createCard(payload: {
  account_id: number;
  card_type?: "virtual" | "physical";
  label?: string;
  spending_limit?: number;
}) {
  const { data } = await api.post("/cards", payload);
  return data;
}

export async function freezeCard(cardId: number) {
  const { data } = await api.post(`/cards/${cardId}/freeze`);
  return data;
}

export async function unfreezeCard(cardId: number) {
  const { data } = await api.post(`/cards/${cardId}/unfreeze`);
  return data;
}

export async function getNotifications(limit = 30) {
  const { data } = await api.get("/notifications", { params: { limit } });
  return data;
}

export async function markNotificationsRead(ids?: number[]) {
  const { data } = await api.post("/notifications/read", ids ?? null);
  return data;
}

export function getWsUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  return `${base.replace(/^http/, "ws")}/notifications/ws`;
}

export async function getPaymentConfig() {
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
  const { data } = await api.get("/baas/dashboard");
  return data;
}

export async function listBaasAccounts() {
  const { data } = await api.get("/baas/accounts");
  return data;
}

export async function openBaasAccount(payload: {
  name: string;
  deposit_product?: "checking" | "savings" | "wallet";
  initial_deposit?: number;
}) {
  const { data } = await api.post("/baas/accounts", payload);
  return data;
}

export async function createBaasPayment(payload: any) {
  const { data } = await api.post("/baas/payments", payload);
  return data;
}

export async function listBaasPayments(limit = 50) {
  const { data } = await api.get("/baas/payments", { params: { limit } });
  return data;
}

export async function listBaasCards() {
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
  const { data } = await api.get("/baas/credit-accounts");
  return data;
}

export async function openCreditAccount(payload: {
  name: string;
  credit_terms?: string;
  credit_limit?: number;
}) {
  const { data } = await api.post("/baas/credit-accounts", payload);
  return data;
}

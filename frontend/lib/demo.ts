/**
 * Offline demo dataset — used when the FastAPI backend is unreachable
 * (typical on Vercel if NEXT_PUBLIC_API_URL is unset or the API is down).
 * Marked clearly in the UI so nobody mistakes it for a live bank session.
 */

export const DEMO_FLAG = "modernbank_demo_mode";

export function isDemoMode(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return localStorage.getItem(DEMO_FLAG) === "1";
  } catch {
    return false;
  }
}

export function enterDemoMode() {
  try {
    localStorage.setItem(DEMO_FLAG, "1");
    localStorage.setItem("access_token", "demo-token");
    sessionStorage.setItem(DEMO_FLAG, "1");
    sessionStorage.setItem("access_token", "demo-token");
  } catch {
    /* storage blocked */
  }
}

/** Only clears the demo flag — never touches real JWT tokens. */
export function exitDemoMode() {
  try {
    localStorage.removeItem(DEMO_FLAG);
    sessionStorage.removeItem(DEMO_FLAG);
    // If the token is the placeholder demo token, clear it; leave real JWTs alone
    if (localStorage.getItem("access_token") === "demo-token") {
      localStorage.removeItem("access_token");
    }
    if (sessionStorage.getItem("access_token") === "demo-token") {
      sessionStorage.removeItem("access_token");
    }
  } catch {
    /* storage blocked */
  }
}

export const demoUser = {
  id: 1,
  email: "demo@modernbank.dev",
  full_name: "Alex Rivera",
  role: "customer",
  is_active: true,
  is_verified: true,
  kyc_status: "verified",
  phone: "+1-555-0100",
};

export const demoAdmin = {
  id: 99,
  email: "admin@modernbank.dev",
  full_name: "System Administrator",
  role: "admin",
  is_active: true,
  is_verified: true,
  kyc_status: "verified",
};

export const demoAccounts = [
  {
    id: 1,
    account_number: "482910374651",
    account_type: "checking",
    balance: 4250.75,
    currency: "USD",
    is_active: true,
  },
  {
    id: 2,
    account_number: "482910374652",
    account_type: "savings",
    balance: 12500.0,
    currency: "USD",
    is_active: true,
  },
];

export const demoTransactions = [
  {
    id: 1,
    amount: 1200,
    type: "transfer_in",
    status: "completed",
    description: "Payroll — Acme Corp",
    reference: "TXN-DEMO000001",
    is_flagged: false,
    fraud_score: 0,
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
  {
    id: 2,
    amount: 84.5,
    type: "transfer_out",
    status: "completed",
    description: "Transfer to •••• 2201",
    reference: "TXN-DEMO000002",
    is_flagged: false,
    fraud_score: 0.12,
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 3,
    amount: 2500,
    type: "transfer_out",
    status: "flagged",
    description: "Large transfer — review",
    reference: "TXN-DEMO000003",
    is_flagged: true,
    fraud_score: 0.72,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 4,
    amount: 45.99,
    type: "payment",
    status: "completed",
    description: "Card · Everyday · CLOUDFLARE",
    reference: "TXN-DEMO000004",
    is_flagged: false,
    fraud_score: 0.05,
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
];

export const demoCards = [
  {
    id: 1,
    card_number_masked: "•••• •••• •••• 4242",
    last_four: "4242",
    card_type: "virtual",
    status: "active",
    expiry_month: 9,
    expiry_year: 2029,
    spending_limit: 2500,
    label: "Everyday",
  },
];

export const demoDashboard = {
  total_balance: 16750.75,
  accounts: demoAccounts,
  recent_transactions: demoTransactions,
  monthly_spending: 2630.49,
  monthly_income: 1200,
  savings_progress: 42.5,
};

export const demoInsights = [
  {
    title: "Idle cash opportunity",
    message:
      "You have $12,500 in savings. Consider a high-yield allocation for amounts above your emergency fund.",
    category: "investment",
    confidence: 0.78,
  },
  {
    title: "One transfer under review",
    message:
      "A $2,500 outbound transfer was flagged (high amount + velocity). It will clear after review in the live API.",
    category: "spending",
    confidence: 0.9,
  },
];

export const demoGoals = [
  { id: 1, name: "Emergency fund", target_amount: 10000, current_amount: 4200 },
  { id: 2, name: "Tokyo trip", target_amount: 3000, current_amount: 900 },
];

export const demoNotifications = [
  {
    id: 1,
    title: "Transfer under review",
    message: "Your transfer of $2,500 was flagged. Ref: TXN-DEMO000003",
    type: "fraud",
    is_read: false,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 2,
    title: "Money received",
    message: "You received $1,200.00 from Acme Corp.",
    type: "transfer",
    is_read: true,
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
];

export const demoAdminStats = {
  total_users: 128,
  active_users: 114,
  total_accounts: 241,
  total_balance: 1842290.42,
  transaction_volume_24h: 42890.12,
  flagged_transactions: 3,
  new_users_today: 4,
};

export const demoAdminUsers = [
  demoUser,
  demoAdmin,
  {
    id: 3,
    email: "jordan@example.com",
    full_name: "Jordan Lee",
    role: "customer",
    is_active: true,
    kyc_status: "pending",
  },
];

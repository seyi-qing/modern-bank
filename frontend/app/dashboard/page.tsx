"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getDashboard, getCards } from "@/lib/api";
import { formatMoney, formatDateTime, maskAccount, cn } from "@/lib/format";
import { Card, CardTitle } from "@/components/ui/Card";
import {
  ArrowUpRight,
  ArrowDownLeft,
  CreditCard,
  Wallet,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

type Dash = {
  total_balance: number;
  accounts: any[];
  recent_transactions: any[];
  monthly_spending: number;
  monthly_income: number;
  savings_progress: number;
};

export default function DashboardOverview() {
  const [data, setData] = useState<Dash | null>(null);
  const [cards, setCards] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getDashboard(), getCards().catch(() => [])])
      .then(([d, c]) => {
        setData(d);
        setCards(Array.isArray(c) ? c : c?.cards ?? []);
      })
      .catch(() => setError("Could not load dashboard. Is the API running?"));
  }, []);

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-red-300">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex justify-center py-24">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const primaryCard = cards.find((c) => c.status === "active") ?? cards[0];

  return (
    <div className="space-y-8">
      <header className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500 mb-1">Total balance</p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
            {formatMoney(data.total_balance)}
          </h1>
        </div>
        <div className="flex gap-2">
          <Link
            href="/dashboard/transfer"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-sm font-medium text-white transition"
          >
            <ArrowUpRight className="w-4 h-4" />
            Send
          </Link>
          <Link
            href="/dashboard/deposit"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-white/10 hover:bg-white/5 text-sm font-medium transition"
          >
            <ArrowDownLeft className="w-4 h-4" />
            Add funds
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Stat
          label="Income (30d)"
          value={formatMoney(data.monthly_income)}
          icon={<TrendingUp className="w-4 h-4 text-emerald-400" />}
        />
        <Stat
          label="Spending (30d)"
          value={formatMoney(data.monthly_spending)}
          icon={<TrendingDown className="w-4 h-4 text-amber-400" />}
        />
        <Stat
          label="Accounts"
          value={String(data.accounts?.length ?? 0)}
          icon={<Wallet className="w-4 h-4 text-brand-400" />}
        />
        <Stat
          label="Savings goals"
          value={`${data.savings_progress.toFixed(0)}%`}
          icon={<CreditCard className="w-4 h-4 text-violet-400" />}
        />
      </div>

      <div className="grid lg:grid-cols-5 gap-4 sm:gap-6">
        <div className="lg:col-span-3 space-y-4">
          <Card>
            <CardTitle>Accounts</CardTitle>
            <ul className="space-y-3">
              {(data.accounts || []).map((a) => (
                <li
                  key={a.id}
                  className="flex items-center justify-between py-3 border-b border-white/5 last:border-0"
                >
                  <div>
                    <p className="font-medium capitalize text-white">
                      {a.account_type} · {maskAccount(a.account_number)}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">{a.currency}</p>
                  </div>
                  <p className="font-semibold tabular-nums text-white">
                    {formatMoney(a.balance, a.currency)}
                  </p>
                </li>
              ))}
            </ul>
          </Card>

          <Card>
            <div className="flex items-center justify-between mb-3">
              <CardTitle className="mb-0">Recent activity</CardTitle>
              <Link
                href="/dashboard/transactions"
                className="text-xs text-brand-400 hover:text-brand-300"
              >
                View all
              </Link>
            </div>
            <ul className="space-y-1">
              {(data.recent_transactions || []).slice(0, 6).map((tx) => {
                const out = String(tx.type || "").includes("out") ||
                  String(tx.type || "").includes("payment") ||
                  String(tx.type || "").includes("withdraw");
                return (
                  <li
                    key={tx.id}
                    className="flex items-center justify-between py-2.5 gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div
                        className={cn(
                          "w-9 h-9 rounded-full flex items-center justify-center shrink-0",
                          out ? "bg-red-500/15" : "bg-emerald-500/15"
                        )}
                      >
                        {out ? (
                          <ArrowUpRight className="w-4 h-4 text-red-400" />
                        ) : (
                          <ArrowDownLeft className="w-4 h-4 text-emerald-400" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate text-white">
                          {tx.description || tx.type}
                        </p>
                        <p className="text-xs text-slate-500">
                          {tx.created_at ? formatDateTime(tx.created_at) : "—"}
                          {tx.is_flagged ? " · Flagged" : ""}
                        </p>
                      </div>
                    </div>
                    <p
                      className={cn(
                        "text-sm font-semibold tabular-nums shrink-0",
                        out ? "text-red-300" : "text-emerald-300"
                      )}
                    >
                      {out ? "−" : "+"}
                      {formatMoney(tx.amount)}
                    </p>
                  </li>
                );
              })}
              {!data.recent_transactions?.length && (
                <p className="text-sm text-slate-500 py-4">No transactions yet.</p>
              )}
            </ul>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-4">
          {primaryCard && (
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-600 via-brand-700 to-surface-900 p-6 text-white shadow-glow min-h-[180px]">
              <div className="absolute -right-8 -top-8 w-40 h-40 rounded-full bg-white/10 blur-2xl" />
              <div className="relative flex flex-col h-full justify-between gap-8">
                <div className="flex justify-between items-start">
                  <span className="text-xs uppercase tracking-wider text-white/70">
                    {primaryCard.label || primaryCard.card_type}
                  </span>
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-white/15 capitalize">
                    {primaryCard.status}
                  </span>
                </div>
                <div>
                  <p className="font-mono text-lg tracking-widest">
                    {primaryCard.card_number_masked || `•••• ${primaryCard.last_four}`}
                  </p>
                  <p className="mt-2 text-xs text-white/60">
                    Exp {String(primaryCard.expiry_month).padStart(2, "0")}/
                    {primaryCard.expiry_year}
                    {primaryCard.spending_limit
                      ? ` · Limit ${formatMoney(primaryCard.spending_limit)}`
                      : ""}
                  </p>
                </div>
              </div>
            </div>
          )}

          <Card>
            <CardTitle>Quick actions</CardTitle>
            <div className="grid grid-cols-2 gap-2">
              {[
                { href: "/dashboard/transfer", label: "Transfer" },
                { href: "/dashboard/cards", label: "Cards" },
                { href: "/dashboard/transactions", label: "Activity" },
                { href: "/dashboard/baas", label: "BaaS Hub" },
              ].map((a) => (
                <Link
                  key={a.href}
                  href={a.href}
                  className="rounded-xl border border-white/5 bg-surface-950/50 px-3 py-3 text-sm text-slate-300 hover:border-brand-500/40 hover:text-white transition text-center"
                >
                  {a.label}
                </Link>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <Card className="!p-4">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <p className="text-lg sm:text-xl font-semibold tabular-nums text-white">{value}</p>
    </Card>
  );
}

"use client";

import { useEffect, useState } from "react";
import { getAdminStats, getFlaggedTransactions } from "@/lib/api";
import { formatMoney, formatDateTime } from "@/lib/format";
import { Card, CardTitle } from "@/components/ui/Card";
import { Shield, Users, Flag, Activity } from "lucide-react";
import Link from "next/link";

export default function AdminHome() {
  const [stats, setStats] = useState<any>(null);
  const [flagged, setFlagged] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getAdminStats(), getFlaggedTransactions()])
      .then(([s, f]) => {
        setStats(s);
        setFlagged(Array.isArray(f) ? f : f?.transactions ?? []);
      })
      .catch(() => setError("Failed to load admin data"));
  }, []);

  if (error) {
    return <div className="text-red-300 text-sm">{error}</div>;
  }

  if (!stats) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const tiles = [
    { label: "Total users", value: stats.total_users, icon: Users },
    { label: "Active users", value: stats.active_users, icon: Users },
    { label: "24h volume", value: formatMoney(stats.transaction_volume_24h), icon: Activity },
    { label: "Flagged", value: stats.flagged_transactions, icon: Flag },
    { label: "Book balance", value: formatMoney(stats.total_balance), icon: Shield },
    { label: "New today", value: stats.new_users_today, icon: Users },
  ];

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Shield className="w-6 h-6 text-brand-400" />
          System overview
        </h1>
        <p className="text-sm text-slate-500 mt-1">Ops snapshot for the demo bank</p>
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
        {tiles.map((t) => (
          <Card key={t.label} className="!p-4">
            <div className="flex items-center gap-2 text-slate-500 text-xs mb-2">
              <t.icon className="w-3.5 h-3.5" />
              {t.label}
            </div>
            <p className="text-xl font-semibold text-white tabular-nums">{t.value}</p>
          </Card>
        ))}
      </div>

      <Card>
        <div className="flex items-center justify-between mb-3">
          <CardTitle className="mb-0">Flagged queue</CardTitle>
          <Link href="/admin/flagged" className="text-xs text-brand-400">
            View all
          </Link>
        </div>
        <ul className="space-y-2">
          {flagged.slice(0, 5).map((tx) => (
            <li
              key={tx.id}
              className="flex justify-between gap-3 py-2 border-b border-white/5 last:border-0 text-sm"
            >
              <div>
                <p className="text-white">{tx.description || tx.reference}</p>
                <p className="text-xs text-slate-500">
                  {tx.created_at ? formatDateTime(tx.created_at) : ""}
                  {tx.fraud_score != null
                    ? ` · risk ${(tx.fraud_score * 100).toFixed(0)}%`
                    : ""}
                </p>
              </div>
              <p className="text-amber-300 font-semibold tabular-nums">
                {formatMoney(tx.amount)}
              </p>
            </li>
          ))}
          {!flagged.length && (
            <p className="text-sm text-slate-500">No flagged transactions.</p>
          )}
        </ul>
      </Card>
    </div>
  );
}

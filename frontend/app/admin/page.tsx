"use client";

import { useEffect, useState } from "react";
import {
  getAdminStats,
  getFlaggedTransactions,
  getReconciliation,
} from "@/lib/api";
import { formatMoney, formatMoneyCompact, formatDateTime } from "@/lib/format";
import { Card, CardTitle } from "@/components/ui/Card";
import { Shield, Users, Flag, Activity, Scale } from "lucide-react";
import Link from "next/link";

export default function AdminHome() {
  const [stats, setStats] = useState<any>(null);
  const [flagged, setFlagged] = useState<any[]>([]);
  const [recon, setRecon] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      getAdminStats(),
      getFlaggedTransactions(),
      getReconciliation().catch(() => null),
    ])
      .then(([s, f, r]) => {
        setStats(s);
        setFlagged(Array.isArray(f) ? f : f?.transactions ?? []);
        setRecon(r);
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
    { label: "Total users", value: String(stats.total_users), full: undefined as string | undefined, icon: Users },
    { label: "Active users", value: String(stats.active_users), full: undefined, icon: Users },
    {
      label: "24h volume",
      value: formatMoneyCompact(stats.transaction_volume_24h),
      full: formatMoney(stats.transaction_volume_24h),
      icon: Activity,
    },
    { label: "Flagged", value: String(stats.flagged_transactions), full: undefined, icon: Flag },
    {
      label: "Book balance",
      value: formatMoneyCompact(stats.total_balance),
      full: formatMoney(stats.total_balance),
      icon: Shield,
    },
    { label: "New today", value: String(stats.new_users_today), full: undefined, icon: Users },
  ];

  return (
    <div className="space-y-6 sm:space-y-8">
      <header className="pr-2">
        <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
          <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-brand-400 shrink-0" />
          <span className="leading-tight">System overview</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Ops snapshot · Banking Core v2.1 ledger enabled
        </p>
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-2.5 sm:gap-3">
        {tiles.map((t) => (
          <Card key={t.label} className="!p-3 sm:!p-4 min-w-0">
            <div className="flex items-center gap-1.5 text-slate-500 text-[10px] sm:text-xs mb-1.5 sm:mb-2">
              <t.icon className="w-3 h-3 sm:w-3.5 sm:h-3.5 shrink-0" />
              <span className="truncate">{t.label}</span>
            </div>
            <p
              className="text-base sm:text-xl font-semibold text-white tabular-nums leading-tight break-all"
              title={t.full || t.value}
            >
              {t.value}
            </p>
            {t.full && t.full !== t.value && (
              <p className="text-[10px] text-slate-500 mt-1 truncate" title={t.full}>
                {t.full}
              </p>
            )}
          </Card>
        ))}
      </div>

      {recon && (
        <Card>
          <div className="flex items-center justify-between gap-2 mb-2">
            <CardTitle className="mb-0 flex items-center gap-2 text-sm sm:text-base">
              <Scale className="w-4 h-4 text-brand-400 shrink-0" />
              Ledger reconciliation
            </CardTitle>
            <Link href="/admin/reconciliation" className="text-xs text-brand-400 shrink-0">
              Full report
            </Link>
          </div>
          <p className={`text-sm font-medium ${recon.ok ? "text-emerald-300" : "text-amber-300"}`}>
            {recon.ok
              ? `OK — ${recon.accounts_balanced}/${recon.accounts_checked} accounts balanced`
              : `Drift — ${recon.accounts_out_of_balance} account(s) out of balance`}
          </p>
        </Card>
      )}

      <Card>
        <div className="flex items-center justify-between gap-2 mb-3">
          <CardTitle className="mb-0">Flagged queue</CardTitle>
          <Link href="/admin/flagged" className="text-xs text-brand-400 shrink-0">
            Review all
          </Link>
        </div>
        <ul className="space-y-2">
          {flagged.slice(0, 5).map((tx) => (
            <li
              key={tx.id}
              className="flex justify-between gap-3 py-2 border-b border-white/5 last:border-0 text-sm"
            >
              <div className="min-w-0">
                <p className="text-white truncate">{tx.description || tx.reference}</p>
                <p className="text-xs text-slate-500">
                  {tx.created_at ? formatDateTime(tx.created_at) : ""}
                  {tx.fraud_score != null
                    ? ` · risk ${(Number(tx.fraud_score) * 100).toFixed(0)}%`
                    : ""}
                </p>
              </div>
              <p className="text-amber-300 font-semibold tabular-nums shrink-0">
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

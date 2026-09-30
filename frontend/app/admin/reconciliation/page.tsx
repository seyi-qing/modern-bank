"use client";

import { useCallback, useEffect, useState } from "react";
import { getReconciliation } from "@/lib/api";
import { formatMoney, formatMoneyCompact } from "@/lib/format";
import { Card, CardTitle } from "@/components/ui/Card";
import { Scale, RefreshCw, CheckCircle2, AlertTriangle } from "lucide-react";

export default function AdminReconciliationPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    return getReconciliation()
      .then(setData)
      .catch(() => setError("Failed to load reconciliation"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-5 sm:space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 pr-2">
          <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
            <Scale className="w-5 h-5 sm:w-6 sm:h-6 text-brand-400 shrink-0" />
            Reconciliation
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Book vs ledger. Read-only — never edit balances here.
          </p>
        </div>
        <button
          type="button"
          onClick={() => load()}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-white/10 text-sm text-slate-300 hover:bg-white/5 disabled:opacity-50 shrink-0"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && <p className="text-sm text-red-300">{error}</p>}

      {data && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-3">
            <Card className="!p-3 sm:!p-4">
              <p className="text-[10px] sm:text-xs text-slate-500 mb-1">Checked</p>
              <p className="text-lg sm:text-xl font-semibold text-white tabular-nums">
                {data.accounts_checked}
              </p>
            </Card>
            <Card className="!p-3 sm:!p-4">
              <p className="text-[10px] sm:text-xs text-slate-500 mb-1">Balanced</p>
              <p className="text-lg sm:text-xl font-semibold text-emerald-300 tabular-nums">
                {data.accounts_balanced}
              </p>
            </Card>
            <Card className="!p-3 sm:!p-4">
              <p className="text-[10px] sm:text-xs text-slate-500 mb-1">Out of balance</p>
              <p className="text-lg sm:text-xl font-semibold text-amber-300 tabular-nums">
                {data.accounts_out_of_balance}
              </p>
            </Card>
            <Card className="!p-3 sm:!p-4">
              <p className="text-[10px] sm:text-xs text-slate-500 mb-1">Overall</p>
              <p
                className={`text-lg sm:text-xl font-semibold flex items-center gap-1.5 ${
                  data.ok ? "text-emerald-300" : "text-amber-300"
                }`}
              >
                {data.ok ? (
                  <>
                    <CheckCircle2 className="w-5 h-5" /> OK
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-5 h-5" /> Not OK
                  </>
                )}
              </p>
            </Card>
          </div>

          {/* Mobile cards */}
          <div className="space-y-3 md:hidden">
            {(data.results || []).map((r: any) => (
              <Card key={r.account_id} className="!p-4">
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="font-mono text-white text-sm">#{r.account_id}</span>
                  <span className="text-xs text-slate-400">{r.currency}</span>
                  {r.balanced ? (
                    <span className="text-emerald-400 text-xs font-medium">balanced</span>
                  ) : (
                    <span className="text-amber-400 text-xs font-medium">drift</span>
                  )}
                </div>
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <dt className="text-[10px] text-slate-500">Book</dt>
                    <dd className="text-white tabular-nums text-xs sm:text-sm" title={formatMoney(r.book_balance)}>
                      {formatMoneyCompact(r.book_balance)}
                    </dd>
                    <dd className="text-[10px] text-slate-500 tabular-nums truncate">
                      {formatMoney(r.book_balance)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[10px] text-slate-500">Ledger</dt>
                    <dd className="text-white tabular-nums text-xs sm:text-sm" title={formatMoney(r.ledger_balance)}>
                      {formatMoneyCompact(r.ledger_balance)}
                    </dd>
                    <dd className="text-[10px] text-slate-500 tabular-nums truncate">
                      {formatMoney(r.ledger_balance)}
                    </dd>
                  </div>
                </dl>
              </Card>
            ))}
          </div>

          {/* Desktop table with horizontal scroll */}
          <Card className="!p-0 overflow-x-auto hidden md:block">
            <div className="px-5 py-3 border-b border-white/5">
              <CardTitle className="mb-0">Per account</CardTitle>
            </div>
            <table className="w-full text-sm min-w-[720px]">
              <thead>
                <tr className="text-left text-xs text-slate-500 border-b border-white/5">
                  <th className="px-5 py-3">Account</th>
                  <th className="px-5 py-3">Currency</th>
                  <th className="px-5 py-3 text-right">Book</th>
                  <th className="px-5 py-3 text-right">Ledger</th>
                  <th className="px-5 py-3 text-right">Diff</th>
                  <th className="px-5 py-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody>
                {(data.results || []).map((r: any) => (
                  <tr key={r.account_id} className="border-b border-white/5 last:border-0">
                    <td className="px-5 py-3 text-white font-mono">#{r.account_id}</td>
                    <td className="px-5 py-3 text-slate-400">{r.currency}</td>
                    <td className="px-5 py-3 text-right tabular-nums text-white whitespace-nowrap">
                      {formatMoney(r.book_balance)}
                    </td>
                    <td className="px-5 py-3 text-right tabular-nums text-white whitespace-nowrap">
                      {formatMoney(r.ledger_balance)}
                    </td>
                    <td
                      className={`px-5 py-3 text-right tabular-nums whitespace-nowrap ${
                        Number(r.difference) === 0 ? "text-slate-500" : "text-amber-300"
                      }`}
                    >
                      {formatMoney(r.difference)}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {r.balanced ? (
                        <span className="text-emerald-400 text-xs font-medium">balanced</span>
                      ) : (
                        <span className="text-amber-400 text-xs font-medium">drift</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}

      {loading && !data && (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}

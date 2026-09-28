"use client";

import { useCallback, useEffect, useState } from "react";
import { getReconciliation } from "@/lib/api";
import { formatMoney } from "@/lib/format";
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
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Scale className="w-6 h-6 text-brand-400" />
            Reconciliation
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Book balance vs ledger balance. Read-only — never edit balances from
            this screen.
          </p>
        </div>
        <button
          type="button"
          onClick={() => load()}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-white/10 text-sm text-slate-300 hover:bg-white/5 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && <p className="text-sm text-red-300">{error}</p>}

      {data && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Card className="!p-4">
              <p className="text-xs text-slate-500 mb-1">Checked</p>
              <p className="text-xl font-semibold text-white tabular-nums">
                {data.accounts_checked}
              </p>
            </Card>
            <Card className="!p-4">
              <p className="text-xs text-slate-500 mb-1">Balanced</p>
              <p className="text-xl font-semibold text-emerald-300 tabular-nums">
                {data.accounts_balanced}
              </p>
            </Card>
            <Card className="!p-4">
              <p className="text-xs text-slate-500 mb-1">Out of balance</p>
              <p className="text-xl font-semibold text-amber-300 tabular-nums">
                {data.accounts_out_of_balance}
              </p>
            </Card>
            <Card className="!p-4">
              <p className="text-xs text-slate-500 mb-1">Overall</p>
              <p
                className={`text-xl font-semibold flex items-center gap-1.5 ${
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

          <Card className="!p-0 overflow-hidden">
            <div className="px-5 py-3 border-b border-white/5">
              <CardTitle className="mb-0">Per account</CardTitle>
            </div>
            <table className="w-full text-sm">
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
                  <tr
                    key={r.account_id}
                    className="border-b border-white/5 last:border-0"
                  >
                    <td className="px-5 py-3 text-white font-mono">
                      #{r.account_id}
                    </td>
                    <td className="px-5 py-3 text-slate-400">{r.currency}</td>
                    <td className="px-5 py-3 text-right tabular-nums text-white">
                      {formatMoney(r.book_balance)}
                    </td>
                    <td className="px-5 py-3 text-right tabular-nums text-white">
                      {formatMoney(r.ledger_balance)}
                    </td>
                    <td
                      className={`px-5 py-3 text-right tabular-nums ${
                        Number(r.difference) === 0
                          ? "text-slate-500"
                          : "text-amber-300"
                      }`}
                    >
                      {formatMoney(r.difference)}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {r.balanced ? (
                        <span className="text-emerald-400 text-xs font-medium">
                          balanced
                        </span>
                      ) : (
                        <span className="text-amber-400 text-xs font-medium">
                          drift
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!(data.results || []).length && (
              <p className="text-center text-slate-500 text-sm py-10">
                No accounts reported.
              </p>
            )}
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

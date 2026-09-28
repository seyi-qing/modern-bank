"use client";

import { useEffect, useState } from "react";
import { api, hydrateAuthFromStorage, isDemoMode } from "@/lib/api";
import { formatMoney, formatDateTime } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { History } from "lucide-react";

async function fetchAllTransactions() {
  if (typeof window !== "undefined") {
    const { isDemoMode: demo, demoTransactions } = await import("@/lib/demo");
    if (demo()) return demoTransactions;
  }
  hydrateAuthFromStorage();
  const { data } = await api.get("/admin/transactions", { params: { limit: 100 } });
  return data;
}

export default function AdminTransactionsPage() {
  const [txs, setTxs] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchAllTransactions()
      .then((list) => setTxs(Array.isArray(list) ? list : []))
      .catch(() => setError("Failed to load transactions"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <History className="w-6 h-6 text-brand-400" />
          All activity
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Latest transactions across the platform (read-only).
        </p>
      </header>

      {error && <p className="text-sm text-red-300">{error}</p>}

      <Card className="!p-0 overflow-x-auto">
        <table className="w-full text-sm min-w-[520px]">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-white/5">
              <th className="px-4 py-3">When</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            {txs.map((tx) => (
              <tr key={tx.id} className="border-b border-white/5 last:border-0">
                <td className="px-4 py-3 text-slate-400 whitespace-nowrap text-xs">
                  {tx.created_at ? formatDateTime(tx.created_at) : "—"}
                </td>
                <td className="px-4 py-3 text-white">
                  {tx.description || tx.type}
                  <span className="block text-xs text-slate-600 font-mono">
                    {tx.reference}
                    {tx.is_flagged ? " · flagged" : ""}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">{tx.status}</td>
                <td className="px-4 py-3 text-right font-semibold text-white tabular-nums">
                  {formatMoney(tx.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && (
          <p className="text-center text-slate-500 text-sm py-10">Loading…</p>
        )}
        {!loading && !txs.length && (
          <p className="text-center text-slate-500 text-sm py-10">No transactions.</p>
        )}
      </Card>
    </div>
  );
}

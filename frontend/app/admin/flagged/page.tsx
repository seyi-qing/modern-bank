"use client";

import { useEffect, useState } from "react";
import { getFlaggedTransactions } from "@/lib/api";
import { formatMoney, formatDateTime } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { Flag } from "lucide-react";

export default function AdminFlaggedPage() {
  const [txs, setTxs] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getFlaggedTransactions()
      .then((f) => setTxs(Array.isArray(f) ? f : f?.transactions ?? []))
      .catch(() => setError("Failed to load flagged queue"));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Flag className="w-6 h-6 text-amber-400" />
        Flagged transactions
      </h1>
      <p className="text-sm text-slate-500 -mt-3">
        Review queue from the fraud engine. Approve/reject hooks can attach to the admin API next.
      </p>
      {error && <p className="text-sm text-red-300">{error}</p>}
      <Card className="!p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-white/5">
              <th className="px-5 py-3">When</th>
              <th className="px-5 py-3">Description</th>
              <th className="px-5 py-3">Risk</th>
              <th className="px-5 py-3 text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            {txs.map((tx) => (
              <tr key={tx.id} className="border-b border-white/5 last:border-0">
                <td className="px-5 py-3 text-slate-400 whitespace-nowrap">
                  {tx.created_at ? formatDateTime(tx.created_at) : "—"}
                </td>
                <td className="px-5 py-3 text-white">
                  {tx.description}
                  <span className="block text-xs text-slate-600 font-mono">
                    {tx.reference}
                  </span>
                </td>
                <td className="px-5 py-3 text-amber-300">
                  {tx.fraud_score != null
                    ? `${(tx.fraud_score * 100).toFixed(0)}%`
                    : "—"}
                </td>
                <td className="px-5 py-3 text-right font-semibold text-white tabular-nums">
                  {formatMoney(tx.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!txs.length && (
          <p className="text-center text-slate-500 text-sm py-12">Queue is empty.</p>
        )}
      </Card>
    </div>
  );
}

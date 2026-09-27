"use client";

import { useEffect, useState } from "react";
import { getTransactions } from "@/lib/api";
import { formatMoney, formatDateTime, cn } from "@/lib/format";
import { Card, CardTitle } from "@/components/ui/Card";
import { History } from "lucide-react";

export default function TransactionsPage() {
  const [txs, setTxs] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<"all" | "flagged">("all");

  useEffect(() => {
    getTransactions(undefined, 100)
      .then((data) => setTxs(Array.isArray(data) ? data : data?.transactions ?? []))
      .catch(() => setError("Failed to load transactions"));
  }, []);

  const list =
    filter === "flagged" ? txs.filter((t) => t.is_flagged) : txs;

  return (
    <div className="space-y-6">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <History className="w-6 h-6 text-brand-400" />
            Activity
          </h1>
          <p className="text-sm text-slate-500 mt-1">Full transaction ledger</p>
        </div>
        <div className="flex gap-1 p-1 rounded-xl bg-surface-900 border border-white/5">
          {(["all", "flagged"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition",
                filter === f
                  ? "bg-brand-600/30 text-brand-200"
                  : "text-slate-500 hover:text-white"
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </header>

      {error && (
        <div className="text-red-300 text-sm border border-red-500/30 rounded-xl p-4">
          {error}
        </div>
      )}

      <Card className="!p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-white/5">
                <th className="px-5 py-3 font-medium">Date</th>
                <th className="px-5 py-3 font-medium">Description</th>
                <th className="px-5 py-3 font-medium">Type</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {list.map((tx) => {
                const out =
                  String(tx.type || "").includes("out") ||
                  String(tx.type || "").includes("payment") ||
                  String(tx.type || "").includes("withdraw");
                return (
                  <tr
                    key={tx.id}
                    className="border-b border-white/5 last:border-0 hover:bg-white/[0.02]"
                  >
                    <td className="px-5 py-3 text-slate-400 whitespace-nowrap">
                      {tx.created_at ? formatDateTime(tx.created_at) : "—"}
                    </td>
                    <td className="px-5 py-3 text-white max-w-[220px] truncate">
                      {tx.description || "—"}
                      {tx.reference && (
                        <span className="block text-xs text-slate-600 font-mono">
                          {tx.reference}
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3 text-slate-400 capitalize">
                      {String(tx.type || "").replace(/_/g, " ")}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={cn(
                          "text-xs px-2 py-0.5 rounded-full capitalize",
                          tx.is_flagged
                            ? "bg-amber-500/15 text-amber-300"
                            : tx.status === "completed"
                            ? "bg-emerald-500/15 text-emerald-300"
                            : "bg-slate-500/15 text-slate-400"
                        )}
                      >
                        {tx.is_flagged ? "flagged" : tx.status}
                      </span>
                    </td>
                    <td
                      className={cn(
                        "px-5 py-3 text-right font-semibold tabular-nums",
                        out ? "text-red-300" : "text-emerald-300"
                      )}
                    >
                      {out ? "−" : "+"}
                      {formatMoney(tx.amount)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!list.length && (
            <p className="text-center text-slate-500 text-sm py-12">
              No transactions to show.
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}

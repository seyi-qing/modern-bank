"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getFlaggedTransactions,
  reviewFlaggedTransaction,
} from "@/lib/api";
import { formatMoney, formatDateTime } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { Flag, Check, X, Loader2 } from "lucide-react";

export default function AdminFlaggedPage() {
  const [txs, setTxs] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [reason, setReason] = useState<Record<number, string>>({});
  const [busyId, setBusyId] = useState<number | null>(null);
  const [message, setMessage] = useState("");

  const load = useCallback(() => {
    setError("");
    return getFlaggedTransactions()
      .then((f) => setTxs(Array.isArray(f) ? f : f?.transactions ?? []))
      .catch(() => setError("Failed to load flagged queue"));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onReview(id: number, action: "approve" | "reject") {
    const r = (reason[id] || "").trim();
    if (r.length < 5) {
      setError("Reason must be at least 5 characters.");
      return;
    }
    setBusyId(id);
    setError("");
    setMessage("");
    try {
      await reviewFlaggedTransaction(id, action, r);
      setMessage(`Transaction #${id} ${action}d.`);
      setReason((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
      await load();
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail || err?.message || "Review failed";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Flag className="w-6 h-6 text-amber-400" />
        Flagged transactions
      </h1>
      <p className="text-sm text-slate-500 -mt-3">
        Approve posts the transfer to the double-entry ledger. Reject fails the
        transfer without moving funds. No balance edit controls.
      </p>

      {error && (
        <p className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
          {error}
        </p>
      )}
      {message && (
        <p className="text-sm text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-3 py-2">
          {message}
        </p>
      )}

      <div className="space-y-4">
        {txs.map((tx) => (
          <Card key={tx.id} className="!p-4 space-y-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-white font-medium">
                  {tx.description || "Flagged transfer"}
                </p>
                <p className="text-xs text-slate-500 font-mono mt-0.5">
                  {tx.reference} · id {tx.id}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {tx.created_at ? formatDateTime(tx.created_at) : "—"}
                  {tx.fraud_score != null
                    ? ` · risk ${(tx.fraud_score * 100).toFixed(0)}%`
                    : ""}
                  {tx.status ? ` · ${tx.status}` : ""}
                </p>
              </div>
              <p className="text-lg font-semibold text-amber-300 tabular-nums">
                {formatMoney(tx.amount)}
              </p>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Review reason (required, min 5 chars)
              </label>
              <input
                value={reason[tx.id] || ""}
                onChange={(e) =>
                  setReason((prev) => ({ ...prev, [tx.id]: e.target.value }))
                }
                placeholder="e.g. Customer verified via support ticket #…"
                className="w-full rounded-xl bg-surface-950 border border-white/10 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-500"
                disabled={busyId === tx.id}
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={busyId === tx.id}
                onClick={() => onReview(tx.id, "approve")}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-600/90 hover:bg-emerald-500 disabled:opacity-50 text-sm font-medium text-white"
              >
                {busyId === tx.id ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Check className="w-4 h-4" />
                )}
                Approve
              </button>
              <button
                type="button"
                disabled={busyId === tx.id}
                onClick={() => onReview(tx.id, "reject")}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-red-600/80 hover:bg-red-500 disabled:opacity-50 text-sm font-medium text-white"
              >
                <X className="w-4 h-4" />
                Reject
              </button>
            </div>
          </Card>
        ))}

        {!txs.length && !error && (
          <Card>
            <p className="text-center text-slate-500 text-sm py-8">
              Queue is empty.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}

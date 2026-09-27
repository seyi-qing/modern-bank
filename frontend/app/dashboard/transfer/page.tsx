"use client";

import { useEffect, useState } from "react";
import { getAccounts, transfer } from "@/lib/api";
import { formatMoney, maskAccount } from "@/lib/format";
import { Card, CardTitle } from "@/components/ui/Card";
import { ArrowLeftRight, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function TransferPage() {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [fromId, setFromId] = useState<number | "">("");
  const [toNumber, setToNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAccounts()
      .then((list) => {
        const arr = Array.isArray(list) ? list : list?.accounts ?? [];
        setAccounts(arr);
        if (arr[0]) setFromId(arr[0].id);
      })
      .catch(() => setError("Failed to load accounts"));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setResult(null);
    const n = parseFloat(amount);
    if (!fromId || !toNumber || !n || n <= 0) {
      setError("Fill all fields with a valid amount.");
      return;
    }
    setLoading(true);
    try {
      const tx = await transfer({
        from_account_id: Number(fromId),
        to_account_number: toNumber.trim(),
        amount: n,
        description: description || undefined,
      });
      setResult(tx);
      setAmount("");
      setDescription("");
      const list = await getAccounts();
      setAccounts(Array.isArray(list) ? list : list?.accounts ?? []);
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Transfer failed";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <ArrowLeftRight className="w-6 h-6 text-brand-400" />
          Transfer
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Internal transfers only in this demo. Fraud scoring runs on every send.
        </p>
      </header>

      <Card>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              From account
            </label>
            <select
              value={fromId}
              onChange={(e) => setFromId(Number(e.target.value))}
              className="w-full rounded-xl bg-surface-950 border border-white/10 px-3 py-2.5 text-sm text-white focus:outline-none focus:border-brand-500"
            >
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.account_type} {maskAccount(a.account_number)} —{" "}
                  {formatMoney(a.balance)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              To account number
            </label>
            <input
              value={toNumber}
              onChange={(e) => setToNumber(e.target.value)}
              placeholder="12-digit account number"
              className="w-full rounded-xl bg-surface-950 border border-white/10 px-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-500"
            />
            <p className="text-xs text-slate-600 mt-1">
              Demo tip: open a second user or use an account number from Admin → Users.
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Amount (USD)
            </label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="w-full rounded-xl bg-surface-950 border border-white/10 px-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">
              Note (optional)
            </label>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Rent, gift, invoice…"
              className="w-full rounded-xl bg-surface-950 border border-white/10 px-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-500"
            />
          </div>

          {error && (
            <div className="flex gap-2 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl p-3">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          {result && (
            <div
              className={`flex gap-2 text-sm rounded-xl p-3 border ${
                result.is_flagged
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-200"
                  : "bg-emerald-500/10 border-emerald-500/30 text-emerald-200"
              }`}
            >
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">
                  {result.is_flagged
                    ? "Transfer flagged for review"
                    : "Transfer completed"}
                </p>
                <p className="text-xs opacity-80 mt-0.5">
                  Ref {result.reference}
                  {result.fraud_score != null
                    ? ` · Risk score ${(result.fraud_score * 100).toFixed(0)}%`
                    : ""}
                </p>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 disabled:opacity-50 font-medium text-white transition"
          >
            {loading ? "Sending…" : "Send transfer"}
          </button>
        </form>
      </Card>
    </div>
  );
}

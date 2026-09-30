"use client";

import { useEffect, useState } from "react";
import { getAdminCardRequests, reviewCardRequest } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { CreditCard } from "lucide-react";

function errMsg(e: any): string {
  const d = e?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x: any) => x.msg || JSON.stringify(x)).join(", ");
  if (!e?.response) return `Network error — is the API up? ${e?.message || ""}`;
  return e?.message || "Request failed";
}

export default function AdminCardRequestsPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);

  async function load() {
    try {
      const data = await getAdminCardRequests();
      setRows(Array.isArray(data) ? data : []);
      setError("");
    } catch (e: any) {
      setError(errMsg(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function review(id: number, action: "approve" | "reject") {
    const reason =
      action === "approve"
        ? "KYC verified — card issued"
        : "Does not meet issuance policy";
    setBusy(id);
    try {
      await reviewCardRequest(id, action, reason);
      await load();
    } catch (e: any) {
      setError(errMsg(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <CreditCard className="w-6 h-6 text-brand-400" />
        Card requests
      </h1>
      {error && <p className="text-sm text-red-300 break-words">{error}</p>}

      <div className="space-y-3">
        {rows.map((r) => (
          <Card key={r.id}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="text-sm">
                <div className="text-white font-medium">
                  Request #{r.id} · {r.card_type}
                </div>
                <div className="text-slate-400 text-xs mt-1">
                  user {r.user_id} · account {r.account_id}
                  {r.label ? ` · ${r.label}` : ""}
                  {r.spending_limit != null ? ` · limit ${r.spending_limit}` : ""}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={busy === r.id}
                  onClick={() => review(r.id, "approve")}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600/80 text-white text-xs font-medium disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  type="button"
                  disabled={busy === r.id}
                  onClick={() => review(r.id, "reject")}
                  className="px-3 py-1.5 rounded-lg bg-red-600/80 text-white text-xs font-medium disabled:opacity-50"
                >
                  Reject
                </button>
              </div>
            </div>
          </Card>
        ))}
        {!rows.length && !error && (
          <p className="text-center text-slate-500 text-sm py-10">No pending requests.</p>
        )}
      </div>
    </div>
  );
}

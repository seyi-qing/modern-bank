"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getCustomer360 } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { ArrowLeft } from "lucide-react";

export default function Customer360Page() {
  const params = useParams();
  const id = Number(params.id);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    getCustomer360(id)
      .then(setData)
      .catch(() => setError("Failed to load customer"));
  }, [id]);

  if (error) return <p className="text-red-300">{error}</p>;
  if (!data) return <p className="text-slate-400">Loading…</p>;

  return (
    <div className="space-y-6">
      <Link href="/admin/users" className="text-sm text-slate-400 flex items-center gap-1 hover:text-white">
        <ArrowLeft className="w-4 h-4" /> Users
      </Link>

      <div>
        <h1 className="text-2xl font-bold text-white">{data.full_name}</h1>
        <p className="text-slate-400 text-sm">{data.email}</p>
        <p className="text-xs text-slate-500 mt-1">
          role: {data.role} · kyc: {data.kyc_status} ·{" "}
          {data.is_active ? "active" : "disabled"}
          {data.open_card_requests > 0 && (
            <span className="text-amber-300"> · {data.open_card_requests} open card request(s)</span>
          )}
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <h2 className="text-sm font-semibold text-white mb-3">Accounts</h2>
          <ul className="space-y-2 text-sm">
            {(data.accounts || []).map((a: any) => (
              <li key={a.id} className="flex justify-between text-slate-300">
                <span>
                  {a.account_type} ···{String(a.account_number).slice(-4)}
                  {!a.is_active && <span className="text-red-300"> (frozen)</span>}
                </span>
                <span className="font-mono text-white">
                  {Number(a.balance).toLocaleString(undefined, { style: "currency", currency: a.currency || "USD" })}
                </span>
              </li>
            ))}
          </ul>
        </Card>
        <Card>
          <h2 className="text-sm font-semibold text-white mb-3">Cards</h2>
          <ul className="space-y-2 text-sm text-slate-300">
            {(data.cards || []).length === 0 && <li className="text-slate-500">No cards</li>}
            {(data.cards || []).map((c: any) => (
              <li key={c.id}>
                •••• {c.last_four} · {c.card_type} · {c.status}
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card>
        <h2 className="text-sm font-semibold text-white mb-3">Recent activity</h2>
        <ul className="space-y-2 text-sm">
          {(data.recent_transactions || []).map((t: any) => (
            <li key={t.id} className="flex justify-between text-slate-400 border-b border-white/5 pb-2">
              <span>
                {t.type} {t.is_flagged ? "· flagged" : ""}
                <span className="block text-xs text-slate-600">{t.reference}</span>
              </span>
              <span className="text-white font-mono">{t.amount}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

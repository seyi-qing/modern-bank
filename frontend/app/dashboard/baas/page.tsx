"use client";

import { useEffect, useState } from "react";
import { getBaasDashboard, listBaasAccounts } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { Card, CardTitle } from "@/components/ui/Card";
import { Building2 } from "lucide-react";

export default function BaasPage() {
  const [dash, setDash] = useState<any>(null);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getBaasDashboard(), listBaasAccounts()])
      .then(([d, a]) => {
        setDash(d);
        setAccounts(Array.isArray(a) ? a : a?.accounts ?? []);
      })
      .catch(() => setError("BaaS API unavailable"));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Building2 className="w-6 h-6 text-brand-400" />
        BaaS Hub
      </h1>
      <p className="text-sm text-slate-500 -mt-3">
        Unit-inspired deposit accounts, wallets, and credit lines (educational model).
      </p>

      {error && (
        <div className="text-red-300 text-sm border border-red-500/30 rounded-xl p-4">{error}</div>
      )}

      {dash && (
        <div className="grid sm:grid-cols-3 gap-3">
          {Object.entries(dash)
            .filter(([, v]) => typeof v === "number")
            .slice(0, 6)
            .map(([k, v]) => (
              <Card key={k} className="!p-4">
                <p className="text-xs text-slate-500 capitalize">{k.replace(/_/g, " ")}</p>
                <p className="text-lg font-semibold text-white mt-1">
                  {typeof v === "number" && k.includes("balance")
                    ? formatMoney(v as number)
                    : String(v)}
                </p>
              </Card>
            ))}
        </div>
      )}

      <Card>
        <CardTitle>Deposit accounts</CardTitle>
        <ul className="space-y-3">
          {accounts.map((a) => (
            <li
              key={a.id}
              className="flex justify-between py-2 border-b border-white/5 last:border-0"
            >
              <div>
                <p className="text-sm font-medium text-white">{a.name}</p>
                <p className="text-xs text-slate-500">
                  {a.deposit_product} · {a.account_number}
                </p>
              </div>
              <p className="font-semibold text-white">{formatMoney(a.available ?? a.balance)}</p>
            </li>
          ))}
          {!accounts.length && (
            <p className="text-sm text-slate-500">No BaaS accounts returned.</p>
          )}
        </ul>
      </Card>
    </div>
  );
}

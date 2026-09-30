"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAdminUsers, updateAdminUser } from "@/lib/api";
import { useUserStore } from "@/lib/store";
import { Card } from "@/components/ui/Card";
import { Users, Search } from "lucide-react";

const STAFF_ROLES = [
  "customer",
  "admin",
  "operations",
  "risk_analyst",
  "finance",
  "card_operations",
  "compliance",
  "auditor",
];

function errMsg(e: any): string {
  const d = e?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x: any) => x.msg || JSON.stringify(x)).join(", ");
  return e?.message || "Request failed";
}

export default function AdminUsersPage() {
  const me = useUserStore((s) => s.user);
  const [users, setUsers] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);

  async function load(search?: string) {
    try {
      const u = await getAdminUsers(search);
      setUsers(Array.isArray(u) ? u : u?.users ?? []);
      setError("");
    } catch (e: any) {
      setError(errMsg(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function setRole(userId: number, role: string) {
    if (me?.role !== "admin") {
      setError("Only admin can change roles");
      return;
    }
    setBusy(userId);
    setError("");
    try {
      await updateAdminUser(userId, { role });
      await load(q || undefined);
    } catch (e: any) {
      setError(errMsg(e));
      await load(q || undefined);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Users className="w-6 h-6 text-brand-400" />
        Users
      </h1>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load(q)}
            placeholder="Search email, name, phone…"
            className="w-full pl-10 pr-3 py-2.5 rounded-xl bg-surface-900 border border-white/10 text-sm text-white"
          />
        </div>
        <button
          type="button"
          onClick={() => load(q)}
          className="px-4 py-2 rounded-xl bg-brand-600 text-white text-sm font-medium"
        >
          Search
        </button>
      </div>

      {error && <p className="text-sm text-red-300 break-words">{error}</p>}

      <Card className="!p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-white/5">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">KYC</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-white/5 last:border-0">
                <td className="px-4 py-3">
                  <Link
                    href={`/admin/users/${u.id}`}
                    className="text-brand-300 hover:underline font-medium"
                  >
                    {u.full_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-400 text-xs">{u.email}</td>
                <td className="px-4 py-3">
                  {me?.role === "admin" ? (
                    <select
                      value={u.role}
                      disabled={busy === u.id}
                      onChange={(e) => setRole(u.id, e.target.value)}
                      className="bg-surface-800 border border-white/10 rounded-lg text-xs text-white px-2 py-1 max-w-[9rem]"
                    >
                      {STAFF_ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="capitalize text-slate-300">{u.role}</span>
                  )}
                </td>
                <td className="px-4 py-3 capitalize text-slate-400">{u.kyc_status}</td>
                <td className="px-4 py-3">
                  <span className={u.is_active ? "text-xs text-emerald-300" : "text-xs text-slate-500"}>
                    {u.is_active ? "active" : "disabled"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!users.length && (
          <p className="text-center text-slate-500 text-sm py-10">No users.</p>
        )}
      </Card>
    </div>
  );
}

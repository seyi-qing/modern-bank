"use client";

import { useEffect, useState } from "react";
import { getAdminUsers } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Users } from "lucide-react";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getAdminUsers()
      .then((u) => setUsers(Array.isArray(u) ? u : u?.users ?? []))
      .catch(() => setError("Failed to load users"));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Users className="w-6 h-6 text-brand-400" />
        Users
      </h1>
      {error && <p className="text-sm text-red-300">{error}</p>}
      <Card className="!p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500 border-b border-white/5">
              <th className="px-5 py-3">Name</th>
              <th className="px-5 py-3">Email</th>
              <th className="px-5 py-3">Role</th>
              <th className="px-5 py-3">KYC</th>
              <th className="px-5 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-white/5 last:border-0">
                <td className="px-5 py-3 text-white">{u.full_name}</td>
                <td className="px-5 py-3 text-slate-400">{u.email}</td>
                <td className="px-5 py-3 capitalize text-slate-300">{u.role}</td>
                <td className="px-5 py-3 capitalize text-slate-400">{u.kyc_status}</td>
                <td className="px-5 py-3">
                  <span
                    className={
                      u.is_active
                        ? "text-xs text-emerald-300"
                        : "text-xs text-slate-500"
                    }
                  >
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

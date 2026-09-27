"use client";

import { useEffect, useState } from "react";
import { getGoals, createGoal } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import { Card, CardTitle } from "@/components/ui/Card";
import { Target } from "lucide-react";

export default function GoalsPage() {
  const [goals, setGoals] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [target, setTarget] = useState("");
  const [error, setError] = useState("");

  async function reload() {
    const g = await getGoals();
    setGoals(Array.isArray(g) ? g : g?.goals ?? []);
  }

  useEffect(() => {
    reload().catch(() => setError("Goals API unavailable"));
  }, []);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createGoal({ name, target_amount: parseFloat(target) });
      setName("");
      setTarget("");
      await reload();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Could not create goal");
    }
  }

  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Target className="w-6 h-6 text-brand-400" />
        Savings goals
      </h1>
      {error && <p className="text-sm text-red-300">{error}</p>}
      <Card>
        <form onSubmit={onCreate} className="space-y-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Goal name"
            required
            className="w-full rounded-xl bg-surface-950 border border-white/10 px-3 py-2.5 text-sm text-white"
          />
          <input
            type="number"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Target amount"
            required
            min="1"
            className="w-full rounded-xl bg-surface-950 border border-white/10 px-3 py-2.5 text-sm text-white"
          />
          <button type="submit" className="px-4 py-2 rounded-xl bg-brand-600 text-sm font-medium text-white">
            Add goal
          </button>
        </form>
      </Card>
      <Card>
        <CardTitle>Your goals</CardTitle>
        <ul className="space-y-4">
          {goals.map((g) => {
            const pct = g.target_amount
              ? Math.min(100, (g.current_amount / g.target_amount) * 100)
              : 0;
            return (
              <li key={g.id}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-white font-medium">{g.name}</span>
                  <span className="text-slate-400">
                    {formatMoney(g.current_amount)} / {formatMoney(g.target_amount)}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-brand-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </li>
            );
          })}
          {!goals.length && <p className="text-sm text-slate-500">No goals yet.</p>}
        </ul>
      </Card>
    </div>
  );
}

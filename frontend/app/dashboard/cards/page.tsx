"use client";

import { useEffect, useState } from "react";
import {
  getCards,
  getAccounts,
  createCard,
  freezeCard,
  unfreezeCard,
} from "@/lib/api";
import { formatMoney, cn } from "@/lib/format";
import { Card, CardTitle } from "@/components/ui/Card";
import { CreditCard, Snowflake, Sun, Plus } from "lucide-react";

export default function CardsPage() {
  const [cards, setCards] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [busy, setBusy] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  async function reload() {
    const [c, a] = await Promise.all([
      getCards(),
      getAccounts().catch(() => []),
    ]);
    setCards(Array.isArray(c) ? c : c?.cards ?? []);
    setAccounts(Array.isArray(a) ? a : a?.accounts ?? []);
  }

  useEffect(() => {
    reload().catch(() => setError("Failed to load cards"));
  }, []);

  async function toggleFreeze(card: any) {
    setBusy(card.id);
    try {
      if (card.status === "frozen") await unfreezeCard(card.id);
      else await freezeCard(card.id);
      await reload();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Action failed");
    } finally {
      setBusy(null);
    }
  }

  async function issueCard() {
    if (!accounts[0]) {
      setError("No account to attach a card to");
      return;
    }
    setCreating(true);
    setError("");
    try {
      await createCard({
        account_id: accounts[0].id,
        card_type: "virtual",
        label: "Virtual",
        spending_limit: 1500,
      });
      await reload();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Could not issue card");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <CreditCard className="w-6 h-6 text-brand-400" />
            Cards
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Issue, freeze, and manage virtual cards
          </p>
        </div>
        <button
          onClick={issueCard}
          disabled={creating}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-sm font-medium text-white disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          {creating ? "Issuing…" : "Issue virtual card"}
        </button>
      </header>

      {error && (
        <div className="text-red-300 text-sm border border-red-500/30 rounded-xl p-4">
          {error}
        </div>
      )}

      <div className="grid sm:grid-cols-2 gap-4">
        {cards.map((card) => (
          <div
            key={card.id}
            className={cn(
              "relative overflow-hidden rounded-2xl p-6 min-h-[200px] flex flex-col justify-between",
              card.status === "frozen"
                ? "bg-slate-800 border border-white/10"
                : "bg-gradient-to-br from-brand-600 via-brand-700 to-surface-900 shadow-glow"
            )}
          >
            <div className="flex justify-between items-start">
              <span className="text-xs uppercase tracking-wider text-white/70">
                {card.label || card.card_type}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-white/15 capitalize text-white">
                {card.status}
              </span>
            </div>
            <div>
              <p className="font-mono text-lg tracking-widest text-white">
                {card.card_number_masked || `•••• ${card.last_four}`}
              </p>
              <p className="mt-2 text-xs text-white/60">
                Exp {String(card.expiry_month).padStart(2, "0")}/{card.expiry_year}
                {card.spending_limit
                  ? ` · Limit ${formatMoney(card.spending_limit)}`
                  : ""}
              </p>
            </div>
            <button
              onClick={() => toggleFreeze(card)}
              disabled={busy === card.id || card.status === "cancelled"}
              className="mt-4 self-start inline-flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white disabled:opacity-40"
            >
              {card.status === "frozen" ? (
                <>
                  <Sun className="w-3.5 h-3.5" /> Unfreeze
                </>
              ) : (
                <>
                  <Snowflake className="w-3.5 h-3.5" /> Freeze
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      {!cards.length && (
        <Card>
          <CardTitle>No cards yet</CardTitle>
          <p className="text-sm text-slate-400">
            Issue a virtual card linked to your checking account to get started.
          </p>
        </Card>
      )}
    </div>
  );
}

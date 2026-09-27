"use client";

import { Card, CardTitle } from "@/components/ui/Card";
import { PlusCircle } from "lucide-react";
import Link from "next/link";

/** Deposit via Stripe PaymentIntent — wire when NEXT_PUBLIC_STRIPE_KEY + backend payments are live. */
export default function DepositPage() {
  return (
    <div className="max-w-lg mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <PlusCircle className="w-6 h-6 text-brand-400" />
        Add funds
      </h1>
      <Card>
        <CardTitle>Stripe deposit (demo path)</CardTitle>
        <p className="text-sm text-slate-400 leading-relaxed">
          Backend already exposes <code className="text-brand-300">/payments/deposit-intent</code>.
          Connect a Stripe test key, then this page should call{" "}
          <code className="text-brand-300">createDepositIntent</code> and confirm with Stripe Elements.
        </p>
        <p className="text-sm text-slate-500 mt-3">
          Until then, use internal transfers between seeded accounts to move balances.
        </p>
        <Link
          href="/dashboard/transfer"
          className="inline-block mt-5 text-sm text-brand-400 hover:text-brand-300"
        >
          Go to Transfer →
        </Link>
      </Card>
    </div>
  );
}

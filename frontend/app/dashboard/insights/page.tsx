"use client";

import { useEffect, useState } from "react";
import { getInsights } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Sparkles } from "lucide-react";

export default function InsightsPage() {
  const [insights, setInsights] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getInsights()
      .then((d) => setInsights(Array.isArray(d) ? d : d?.insights ?? []))
      .catch(() => setError("Insights unavailable"));
  }, []);

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <Sparkles className="w-6 h-6 text-brand-400" />
        Insights
      </h1>
      <p className="text-sm text-slate-500 -mt-3">
        Rule-based coaching from your balances and outflows (not a licensed advisor).
      </p>
      {error && <p className="text-sm text-red-300">{error}</p>}
      <div className="space-y-3">
        {insights.map((ins, i) => (
          <Card key={i}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-medium text-white">{ins.title}</p>
                <p className="text-sm text-slate-400 mt-1">{ins.message}</p>
              </div>
              <span className="text-xs text-slate-500 shrink-0 capitalize">{ins.category}</span>
            </div>
            {ins.confidence != null && (
              <p className="text-xs text-slate-600 mt-3">
                Confidence {(ins.confidence * 100).toFixed(0)}%
              </p>
            )}
          </Card>
        ))}
        {!insights.length && !error && (
          <p className="text-sm text-slate-500">No insights yet — make a few transfers first.</p>
        )}
      </div>
    </div>
  );
}

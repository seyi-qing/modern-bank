"use client";

import { useState } from "react";
import Link from "next/link";
import { login, getApiBase, readToken } from "@/lib/api";
import { useUserStore } from "@/lib/store";

export default function LoginPage() {
  const setUser = useUserStore((s) => s.setUser);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(email, password);
      const me = data?.user;
      if (!me) {
        throw new Error("Login succeeded but no user returned. Redeploy the API.");
      }
      // Verify token actually stuck in storage before navigating
      const stored = readToken();
      if (!stored) {
        throw new Error(
          "Could not save session (browser storage blocked). Allow cookies/storage for this site and try again."
        );
      }
      setUser(me);
      window.location.assign(me.role === "admin" ? "/admin" : "/dashboard");
    } catch (err: any) {
      const msg = err?.message || "Login failed";
      setError(msg);
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-950 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex w-12 h-12 rounded-xl bg-gradient-to-br from-brand-400 to-brand-700 items-center justify-center font-bold text-lg mb-3 text-white">
            MB
          </div>
          <h1 className="text-2xl font-bold text-white">Sign in</h1>
          <p className="text-slate-400 text-sm mt-1">Sign in to your account</p>
        </div>

        <form
          onSubmit={onSubmit}
          className="space-y-4 bg-surface-900 border border-white/5 rounded-2xl p-6"
        >
          {error && (
            <div className="text-sm text-red-400 bg-red-500/10 rounded-lg px-3 py-2 leading-relaxed">
              {error}
            </div>
          )}

          <div>
            <label className="text-xs text-slate-400">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg bg-surface-950 border border-white/10 px-3 py-2.5 text-sm text-white focus:outline-none focus:border-brand-500"
              required
            />
          </div>
          <div>
            <label className="text-xs text-slate-400">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg bg-surface-950 border border-white/10 px-3 py-2.5 text-sm text-white focus:outline-none focus:border-brand-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 font-medium text-sm text-white disabled:opacity-50"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>

          <p className="text-[11px] text-slate-600 text-center break-all">
            API: {getApiBase()}
          </p>
        </form>

        <p className="text-center text-sm text-slate-500 mt-4">
          No account?{" "}
          <Link href="/register" className="text-brand-400 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}

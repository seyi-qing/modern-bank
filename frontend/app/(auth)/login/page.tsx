"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, getMe, getApiBase } from "@/lib/api";
import { useUserStore } from "@/lib/store";
import { enterDemoMode, demoUser, demoAdmin } from "@/lib/demo";

export default function LoginPage() {
  const router = useRouter();
  const setUser = useUserStore((s) => s.setUser);
  const [email, setEmail] = useState("demo@modernbank.dev");
  const [password, setPassword] = useState("Demo1234!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showOffline, setShowOffline] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setShowOffline(false);
    setLoading(true);
    try {
      const data = await login(email, password);
      // Prefer user from login response (avoids a second /me call that can 401 on SQLite)
      let me = data?.user;
      if (!me) {
        me = await getMe();
      }
      setUser(me);
      router.push(me.role === "admin" ? "/admin" : "/dashboard");
    } catch (err: any) {
      const msg = err?.message || "Login failed";
      setError(msg);
      if (err?.isNetwork) setShowOffline(true);
    } finally {
      setLoading(false);
    }
  }

  function startOffline(role: "customer" | "admin") {
    enterDemoMode();
    localStorage.setItem("demo_role", role);
    const user = role === "admin" ? demoAdmin : demoUser;
    setUser(user);
    router.push(role === "admin" ? "/admin" : "/dashboard");
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-950 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex w-12 h-12 rounded-xl bg-gradient-to-br from-brand-400 to-brand-700 items-center justify-center font-bold text-lg mb-3 text-white">
            MB
          </div>
          <h1 className="text-2xl font-bold text-white">Sign in</h1>
          <p className="text-slate-400 text-sm mt-1">ModernBank demo</p>
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

        {showOffline && (
          <div className="mt-4 rounded-2xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-3">
            <p className="text-sm text-amber-100/90 leading-relaxed">
              <strong className="text-amber-200">Backend not reachable.</strong>{" "}
              Check the API URL and that the FastAPI project is deployed.
            </p>
            <div className="flex flex-col sm:flex-row gap-2">
              <button
                type="button"
                onClick={() => startOffline("customer")}
                className="flex-1 py-2.5 rounded-lg bg-white/10 hover:bg-white/15 text-sm font-medium text-white"
              >
                Offline demo (customer)
              </button>
              <button
                type="button"
                onClick={() => startOffline("admin")}
                className="flex-1 py-2.5 rounded-lg border border-white/10 hover:bg-white/5 text-sm font-medium text-slate-200"
              >
                Offline demo (admin)
              </button>
            </div>
          </div>
        )}

        <p className="text-center text-sm text-slate-500 mt-4">
          No account?{" "}
          <Link href="/register" className="text-brand-400 hover:underline">
            Register
          </Link>
          {" · "}
          <button
            type="button"
            onClick={() => startOffline("customer")}
            className="text-slate-400 hover:text-white underline-offset-2 hover:underline"
          >
            Offline demo
          </button>
        </p>
      </div>
    </div>
  );
}

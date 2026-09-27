"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { register, login } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function set(k: string, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      await login(form.email, form.password);
      router.replace("/dashboard");
    } catch (err: any) {
      const d = err?.response?.data?.detail;
      setError(typeof d === "string" ? d : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex w-12 h-12 rounded-xl bg-gradient-to-br from-brand-400 to-brand-700 items-center justify-center font-bold text-white mb-4">
            MB
          </div>
          <h1 className="text-2xl font-bold text-white">Open an account</h1>
          <p className="text-sm text-slate-500 mt-1">ModernBank demo — not a real bank</p>
        </div>

        <form
          onSubmit={onSubmit}
          className="rounded-2xl border border-white/5 bg-surface-900/80 p-6 space-y-4"
        >
          {(
            [
              ["full_name", "Full name", "text"],
              ["email", "Email", "email"],
              ["phone", "Phone (optional)", "tel"],
              ["password", "Password", "password"],
            ] as const
          ).map(([key, label, type]) => (
            <div key={key}>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">
                {label}
              </label>
              <input
                type={type}
                required={key !== "phone"}
                value={(form as any)[key]}
                onChange={(e) => set(key, e.target.value)}
                className="w-full rounded-xl bg-surface-950 border border-white/10 px-3 py-2.5 text-sm text-white focus:outline-none focus:border-brand-500"
              />
            </div>
          ))}

          {error && (
            <p className="text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-brand-600 hover:bg-brand-500 font-medium text-white disabled:opacity-50"
          >
            {loading ? "Creating…" : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-brand-400 hover:text-brand-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

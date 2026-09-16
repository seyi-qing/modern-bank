import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-surface-950 flex flex-col">
      <header className="border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-brand-700 flex items-center justify-center font-bold text-sm">
            MB
          </div>
          <span className="font-semibold text-lg">ModernBank</span>
        </div>
        <div className="flex gap-3">
          <Link href="/login" className="px-4 py-2 text-sm text-slate-300 hover:text-white">
            Sign in
          </Link>
          <Link
            href="/register"
            className="px-4 py-2 text-sm rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-medium"
          >
            Open account
          </Link>
        </div>
      </header>
      <main className="flex-1 flex flex-col items-center justify-center px-6 text-center">
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight max-w-2xl">
          Banking that moves at the speed of software
        </h1>
        <p className="mt-4 text-slate-400 max-w-lg">
          Real-time transfers, fraud scoring, cards, and a Unit-inspired BaaS hub.
          Educational demo — not a real bank.
        </p>
        <div className="mt-8 flex gap-4">
          <Link
            href="/register"
            className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 font-medium"
          >
            Get started
          </Link>
          <Link
            href="/login"
            className="px-6 py-3 rounded-xl border border-white/10 hover:bg-white/5 font-medium"
          >
            Demo login
          </Link>
        </div>
        <p className="mt-6 text-xs text-slate-600">
          demo@modernbank.dev / Demo1234!
        </p>
      </main>
    </div>
  );
}

import Link from "next/link";

const features = [
  {
    title: "Real-time transfers",
    body: "Move money between accounts with instant ledger updates and clear debit/credit history.",
  },
  {
    title: "Fraud scoring",
    body: "Every outbound transfer is scored for velocity, amount, and account age before it clears.",
  },
  {
    title: "Cards & controls",
    body: "Issue virtual cards, freeze in one tap, and set spending limits per card.",
  },
  {
    title: "BaaS-shaped core",
    body: "Deposit accounts, wallets, and credit lines modeled after modern banking-as-a-service APIs.",
  },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-surface-950 text-white flex flex-col">
      <header className="border-b border-white/5 px-6 py-4 flex items-center justify-between sticky top-0 z-20 bg-surface-950/80 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-brand-700 flex items-center justify-center font-bold text-sm">
            MB
          </div>
          <span className="font-semibold text-lg">ModernBank</span>
        </div>
        <div className="flex gap-3 items-center">
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

      <main className="flex-1">
        <section className="relative px-6 pt-16 pb-20 sm:pt-24 sm:pb-28 overflow-hidden">
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute top-0 right-0 w-[480px] h-[480px] rounded-full bg-brand-600/20 blur-[120px]" />
            <div className="absolute bottom-0 left-0 w-[360px] h-[360px] rounded-full bg-violet-600/10 blur-[100px]" />
          </div>
          <div className="relative max-w-5xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="text-brand-400 text-sm font-medium mb-4 tracking-wide">
                Educational digital banking prototype
              </p>
              <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.1]">
                Banking that moves at the speed of software
              </h1>
              <p className="mt-5 text-slate-400 text-lg max-w-md leading-relaxed">
                Transfers, fraud scoring, cards, and a Unit-inspired BaaS hub —
                built to demonstrate full-stack banking architecture. Not a real bank.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/login"
                  className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 font-medium"
                >
                  Demo login
                </Link>
                <Link
                  href="/register"
                  className="px-6 py-3 rounded-xl border border-white/10 hover:bg-white/5 font-medium"
                >
                  Create account
                </Link>
              </div>
              <p className="mt-5 text-xs text-slate-600 font-mono">
                demo@modernbank.dev · Demo1234!
              </p>
            </div>

            {/* Product preview card stack */}
            <div className="relative hidden sm:block">
              <div className="rounded-2xl border border-white/10 bg-surface-900/90 p-6 shadow-glow backdrop-blur">
                <p className="text-xs text-slate-500 mb-1">Total balance</p>
                <p className="text-3xl font-bold tracking-tight">$16,750.75</p>
                <div className="mt-6 space-y-3">
                  {[
                    ["Checking ·••• 4651", "$4,250.75"],
                    ["Savings ·••• 4652", "$12,500.00"],
                  ].map(([label, val]) => (
                    <div
                      key={label}
                      className="flex justify-between text-sm py-2 border-t border-white/5"
                    >
                      <span className="text-slate-400">{label}</span>
                      <span className="font-medium tabular-nums">{val}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-6 rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 p-4">
                  <p className="text-[10px] uppercase tracking-wider text-white/60">Everyday</p>
                  <p className="font-mono text-sm tracking-widest mt-3">•••• •••• •••• 4242</p>
                  <p className="text-[10px] text-white/50 mt-2">Exp 09/29 · Limit $2,500</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-white/5 bg-surface-900/40 px-6 py-6">
          <div className="max-w-5xl mx-auto flex flex-wrap justify-center gap-x-10 gap-y-2 text-xs text-slate-500">
            <span>Next.js · FastAPI</span>
            <span>JWT auth</span>
            <span>Fraud heuristics</span>
            <span>BaaS models</span>
            <span>Not FDIC · Demo only</span>
          </div>
        </section>

        <section className="px-6 py-20 max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-2">What you can explore</h2>
          <p className="text-slate-500 text-sm mb-10 max-w-xl">
            Customer dashboard, transfer flow with risk scoring, cards, activity ledger,
            and an admin ops view.
          </p>
          <div className="grid sm:grid-cols-2 gap-4">
            {features.map((f) => (
              <div
                key={f.title}
                className="rounded-2xl border border-white/5 bg-surface-900/60 p-6 hover:border-brand-500/30 transition"
              >
                <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="px-6 pb-24 text-center">
          <div className="max-w-xl mx-auto rounded-2xl border border-white/5 bg-surface-900/80 p-8">
            <h2 className="text-xl font-bold">Try the demo</h2>
            <p className="text-sm text-slate-400 mt-2 mb-6">
              If the API is offline, use <strong className="text-slate-300">Offline demo</strong> on
              the login page to walk the full UI with simulated data.
            </p>
            <Link
              href="/login"
              className="inline-flex px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 font-medium"
            >
              Go to sign in
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/5 px-6 py-6 text-center text-xs text-slate-600">
        ModernBank — educational prototype · Not a licensed bank · No real funds
      </footer>
    </div>
  );
}

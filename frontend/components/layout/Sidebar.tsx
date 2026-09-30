"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUserStore } from "@/lib/store";
import { logout } from "@/lib/api";
import { isStaffRole, staffNavHrefs } from "@/lib/rbac";
import {
  LayoutDashboard, ArrowLeftRight, History, Target, Sparkles,
  Shield, Users, Flag, LogOut, Menu, X, CreditCard, Bell, PlusCircle, Building2, Scale,
} from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

const customerLinks = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/transfer", label: "Transfer", icon: ArrowLeftRight },
  { href: "/dashboard/deposit", label: "Add funds", icon: PlusCircle },
  { href: "/dashboard/baas", label: "BaaS Hub", icon: Building2 },
  { href: "/dashboard/cards", label: "Cards", icon: CreditCard },
  { href: "/dashboard/transactions", label: "Activity", icon: History },
  { href: "/dashboard/goals", label: "Goals", icon: Target },
  { href: "/dashboard/insights", label: "Insights", icon: Sparkles },
  { href: "/dashboard/notifications", label: "Alerts", icon: Bell },
];

const adminLinkDefs = [
  { href: "/admin", label: "System", icon: Shield },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/transactions", label: "All activity", icon: History },
  { href: "/admin/flagged", label: "Flagged", icon: Flag },
  { href: "/admin/reconciliation", label: "Reconciliation", icon: Scale },
  { href: "/admin/card-requests", label: "Card requests", icon: CreditCard },
];

export default function Sidebar() {
  const pathname = usePathname();
  const user = useUserStore((s) => s.user);
  const setUser = useUserStore((s) => s.setUser);
  const [open, setOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  const staff = isStaffRole(user?.role);
  const allowed = new Set(staffNavHrefs(user?.role));
  const links = staff
    ? adminLinkDefs.filter((l) => allowed.has(l.href))
    : customerLinks;

  function handleSignOut() {
    if (signingOut) return;
    setSigningOut(true);
    setOpen(false);
    try {
      setUser(null as any);
    } catch {
      /* */
    }
    logout();
  }

  return (
    <>
      <button
        type="button"
        aria-label="Open menu"
        onClick={() => setOpen(true)}
        className="lg:hidden fixed top-3 left-3 z-40 p-2.5 rounded-xl bg-surface-900 border border-white/10 shadow-lg text-white"
      >
        <Menu className="w-5 h-5" />
      </button>
      {open && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setOpen(false)}
          aria-hidden
        />
      )}
      <aside
        className={clsx(
          "fixed lg:sticky top-0 left-0 z-50 h-[100dvh] w-64 bg-surface-900 border-r border-white/5 flex flex-col transition-transform duration-200",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="h-16 shrink-0 flex items-center justify-between px-5 border-b border-white/5">
          <Link
            href={staff ? "/admin" : "/dashboard"}
            className="flex items-center gap-2"
            onClick={() => setOpen(false)}
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-brand-700 flex items-center justify-center font-bold text-white text-sm">
              MB
            </div>
            <span className="font-semibold text-white">ModernBank</span>
          </Link>
          <button
            type="button"
            aria-label="Close menu"
            onClick={() => setOpen(false)}
            className="lg:hidden text-slate-400 p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 min-h-0 p-3 space-y-1 overflow-y-auto">
          {links.map((link) => {
            const active =
              pathname === link.href ||
              (link.href !== "/admin" && pathname.startsWith(link.href + "/"));
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition",
                  active
                    ? "bg-brand-600/20 text-brand-300"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                )}
              >
                <link.icon className="w-4 h-4 shrink-0" />
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="shrink-0 p-4 border-t border-white/5 bg-surface-900 pb-[max(1rem,env(safe-area-inset-bottom))]">
          <div className="text-xs text-slate-400 truncate">{user?.full_name}</div>
          <div className="text-xs text-slate-600 truncate">
            {user?.email}
            {staff && <span className="ml-1 text-brand-400">· {user?.role}</span>}
          </div>
          <button
            type="button"
            onClick={handleSignOut}
            disabled={signingOut}
            className="mt-3 flex items-center justify-center gap-2 w-full py-2.5 rounded-xl border border-red-500/30 bg-red-500/10 text-sm font-medium text-red-300 hover:bg-red-500/20 disabled:opacity-50 transition"
          >
            <LogOut className="w-4 h-4" />
            {signingOut ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </aside>
    </>
  );
}

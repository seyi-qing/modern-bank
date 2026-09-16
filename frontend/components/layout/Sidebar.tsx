"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUserStore } from "@/lib/store";
import { logout } from "@/lib/api";
import {
  LayoutDashboard, ArrowLeftRight, History, Target, Sparkles,
  Shield, Users, Flag, LogOut, Menu, X, CreditCard, Bell, PlusCircle, Building2,
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

const adminLinks = [
  { href: "/admin", label: "System", icon: Shield },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/flagged", label: "Flagged", icon: Flag },
];

export default function Sidebar() {
  const pathname = usePathname();
  const user = useUserStore((s) => s.user);
  const [open, setOpen] = useState(false);
  const links = user?.role === "admin" ? adminLinks : customerLinks;

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-surface-900 border border-white/10"
      >
        <Menu className="w-5 h-5" />
      </button>
      {open && (
        <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={() => setOpen(false)} />
      )}
      <aside
        className={clsx(
          "fixed lg:sticky top-0 left-0 z-50 h-screen w-64 bg-surface-900 border-r border-white/5 flex flex-col transition-transform duration-200",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="h-16 flex items-center justify-between px-5 border-b border-white/5">
          <Link href={user?.role === "admin" ? "/admin" : "/dashboard"} className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-brand-700 flex items-center justify-center font-bold text-white text-sm">
              MB
            </div>
            <span className="font-semibold">ModernBank</span>
          </Link>
          <button onClick={() => setOpen(false)} className="lg:hidden text-slate-400">
            <X className="w-5 h-5" />
          </button>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition",
                  active ? "bg-brand-600/20 text-brand-300" : "text-slate-400 hover:text-white hover:bg-white/5"
                )}
              >
                <link.icon className="w-4 h-4" />
                {link.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 border-t border-white/5">
          <div className="text-xs text-slate-500 mb-1 truncate">{user?.full_name}</div>
          <div className="text-xs text-slate-600 truncate mb-3">{user?.email}</div>
          <button
            onClick={() => logout()}
            className="flex items-center gap-2 text-sm text-slate-400 hover:text-red-400 transition w-full"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>
    </>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMe, readToken } from "@/lib/api";
import { useUserStore } from "@/lib/store";
import { isDemoMode } from "@/lib/demo";
import { isStaffRole } from "@/lib/rbac";
import Sidebar from "@/components/layout/Sidebar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, setUser } = useUserStore();
  const [demo, setDemo] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setDemo(isDemoMode());
    const token = readToken();
    if (!token) {
      router.replace("/login");
      return;
    }
    getMe()
      .then((me) => {
        // Control plane is for any staff role (admin, operations, risk, …)
        if (!isStaffRole(me.role)) {
          router.replace("/dashboard");
          return;
        }
        setUser(me);
        setReady(true);
      })
      .catch(() => router.replace("/login"));
  }, [router, setUser]);

  if (!ready || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-950">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-surface-950">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden min-w-0">
        {demo && (
          <div className="bg-amber-500/15 border-b border-amber-500/25 text-amber-100 text-xs sm:text-sm px-4 py-2 text-center">
            Offline demo mode (admin) — simulated ops data.
          </div>
        )}
        <div className="p-4 pt-16 sm:p-6 lg:p-8 lg:pt-8 max-w-6xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}

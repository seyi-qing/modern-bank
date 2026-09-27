"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMe, hydrateAuthFromStorage, readToken } from "@/lib/api";
import { useUserStore } from "@/lib/store";
import { isDemoMode } from "@/lib/demo";
import Sidebar from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, setUser } = useUserStore();
  const [demo, setDemo] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setDemo(isDemoMode());

    const token = hydrateAuthFromStorage() || readToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    getMe()
      .then((me) => {
        if (!cancelled) {
          setUser(me);
          setReady(true);
        }
      })
      .catch(() => {
        if (!cancelled) router.replace("/login");
      });

    return () => {
      cancelled = true;
    };
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
      <main className="flex-1 overflow-x-hidden">
        {demo && (
          <div className="bg-amber-500/15 border-b border-amber-500/25 text-amber-100 text-xs sm:text-sm px-4 py-2 text-center">
            Offline demo mode — data is simulated. Deploy the API and set{" "}
            <code className="text-amber-200">NEXT_PUBLIC_API_URL</code> for a live session.
          </div>
        )}
        <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">{children}</div>
      </main>
    </div>
  );
}

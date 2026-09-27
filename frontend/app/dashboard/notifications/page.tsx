"use client";

import { useEffect, useState } from "react";
import { getNotifications, markNotificationsRead } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { Card } from "@/components/ui/Card";
import { Bell } from "lucide-react";

export default function NotificationsPage() {
  const [items, setItems] = useState<any[]>([]);

  async function reload() {
    const n = await getNotifications();
    setItems(Array.isArray(n) ? n : n?.notifications ?? []);
  }

  useEffect(() => {
    reload().catch(() => {});
  }, []);

  async function markAll() {
    await markNotificationsRead();
    await reload();
  }

  return (
    <div className="space-y-6 max-w-xl">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Bell className="w-6 h-6 text-brand-400" />
          Alerts
        </h1>
        <button
          onClick={markAll}
          className="text-xs text-brand-400 hover:text-brand-300"
        >
          Mark all read
        </button>
      </header>
      <div className="space-y-2">
        {items.map((n) => (
          <Card
            key={n.id}
            className={!n.is_read ? "border-brand-500/30" : undefined}
          >
            <p className="text-sm font-medium text-white">{n.title}</p>
            <p className="text-sm text-slate-400 mt-1">{n.message}</p>
            <p className="text-xs text-slate-600 mt-2">
              {n.created_at ? formatDateTime(n.created_at) : ""}
            </p>
          </Card>
        ))}
        {!items.length && (
          <p className="text-sm text-slate-500">No notifications yet.</p>
        )}
      </div>
    </div>
  );
}

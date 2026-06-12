/**
 * Notification Bell.
 *
 * Header notification indicator with dropdown panel.
 */

import { useState } from "react";
import { Bell } from "lucide-react";
import { cn } from "@/lib/utils";

interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  unread: boolean;
}

// Demo notifications (replace with real API in feature phase)
const DEMO_NOTIFICATIONS: Notification[] = [
  { id: "1", title: "Record accessed", message: "Your medical history was viewed by Dr. Sharma", time: "2h ago", unread: true },
  { id: "2", title: "Consent expiring", message: "Pharmacy Access consent expires in 7 days", time: "1d ago", unread: true },
  { id: "3", title: "Integrity verified", message: "All records passed verification", time: "2d ago", unread: false },
];

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const unreadCount = DEMO_NOTIFICATIONS.filter((n) => n.unread).length;

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative flex h-10 w-10 items-center justify-center rounded-md text-neutral-600 hover:bg-neutral-100"
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[10px] font-bold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-2 w-80 rounded-lg border border-neutral-200 bg-white shadow-lg">
            <div className="border-b border-neutral-200 px-4 py-3">
              <h3 className="text-sm font-semibold text-neutral-800">Notifications</h3>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {DEMO_NOTIFICATIONS.map((n) => (
                <div
                  key={n.id}
                  className={cn(
                    "border-b border-neutral-100 px-4 py-3 hover:bg-neutral-50",
                    n.unread && "bg-primary-50/30"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-sm font-medium text-neutral-800">{n.title}</span>
                    <span className="text-xs text-neutral-400">{n.time}</span>
                  </div>
                  <p className="mt-0.5 text-xs text-neutral-500">{n.message}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

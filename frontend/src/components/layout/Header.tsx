/**
 * Application Header.
 *
 * Contains notification bell, user profile, and logout.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LogOut, User as UserIcon, ChevronDown, Menu } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { NotificationBell } from "./NotificationBell";
import { humanize } from "@/lib/utils";

interface HeaderProps {
  onMenuClick?: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  if (!user) return null;

  return (
    <header className="flex h-16 items-center justify-between border-b border-neutral-200 bg-white px-4 lg:px-6">
      {/* Mobile menu button */}
      <button
        onClick={onMenuClick}
        className="flex h-10 w-10 items-center justify-center rounded-md text-neutral-600 hover:bg-neutral-100 lg:hidden"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="flex-1" />

      <div className="flex items-center gap-2">
        <NotificationBell />

        {/* Profile dropdown */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="flex items-center gap-2 rounded-md px-2 py-1.5 hover:bg-neutral-100"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <div className="hidden text-left md:block">
              <div className="text-sm font-medium text-neutral-800">{user.full_name}</div>
              <div className="text-xs text-neutral-400">{humanize(user.role)}</div>
            </div>
            <ChevronDown className="h-4 w-4 text-neutral-400" />
          </button>

          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 z-20 mt-2 w-56 rounded-lg border border-neutral-200 bg-white shadow-lg">
                <div className="border-b border-neutral-200 px-4 py-3">
                  <div className="text-sm font-medium text-neutral-800">{user.full_name}</div>
                  <div className="text-xs text-neutral-400">{user.email}</div>
                </div>
                <div className="p-1">
                  <button
                    onClick={() => { setMenuOpen(false); navigate("/profile"); }}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-neutral-600 hover:bg-neutral-50"
                  >
                    <UserIcon className="h-4 w-4" />
                    Profile
                  </button>
                  <button
                    onClick={logout}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-danger hover:bg-danger/5"
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

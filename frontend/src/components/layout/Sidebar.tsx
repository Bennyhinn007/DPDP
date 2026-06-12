/**
 * Sidebar Navigation.
 *
 * Role-based navigation menu with active state highlighting.
 */

import { NavLink } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { getNavItemsForRole } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const { user } = useAuth();
  if (!user) return null;

  const navItems = getNavItemsForRole(user.role);

  return (
    <aside className="hidden w-64 flex-shrink-0 flex-col border-r border-neutral-200 bg-white lg:flex">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-neutral-200 px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600">
          <ShieldCheck className="h-5 w-5 text-white" />
        </div>
        <div>
          <div className="text-sm font-semibold text-neutral-800">DPDP Health</div>
          <div className="text-xs text-neutral-400">Secure Platform</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary-50 text-primary-700"
                  : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900"
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-neutral-200 p-4">
        <div className="rounded-md bg-success/5 px-3 py-2 text-xs text-success">
          <div className="font-medium">DPDP Compliant</div>
          <div className="text-success/70">Data residency: India</div>
        </div>
      </div>
    </aside>
  );
}

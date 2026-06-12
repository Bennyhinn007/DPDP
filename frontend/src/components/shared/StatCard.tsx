/**
 * Statistics Card.
 *
 * Dashboard metric display with icon, value, and label.
 */

import { type LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  variant?: "primary" | "success" | "warning" | "secondary";
  subtitle?: string;
}

const variantStyles = {
  primary: "bg-primary-50 text-primary-600",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  secondary: "bg-secondary/10 text-secondary",
};

export function StatCard({ label, value, icon: Icon, variant = "primary", subtitle }: StatCardProps) {
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-neutral-500">{label}</p>
          <p className="mt-2 text-3xl font-bold text-neutral-800">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-neutral-400">{subtitle}</p>}
        </div>
        <div className={cn("flex h-12 w-12 items-center justify-center rounded-lg", variantStyles[variant])}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </Card>
  );
}

/**
 * Compliance Dashboard.
 *
 * Detailed compliance score breakdown by category with risk indicators.
 */

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Lock,
  ShieldCheck,
  ClipboardList,
  Link2,
  Scale,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";
import { complianceService } from "@/services/complianceService";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ComplianceGauge } from "@/components/shared/ComplianceGauge";

interface CategoryMeta {
  key: keyof NonNullable<Awaited<ReturnType<typeof complianceService.getScore>>>["breakdown"];
  label: string;
  max: number;
  icon: typeof Lock;
}

const CATEGORIES: CategoryMeta[] = [
  { key: "encryption", label: "Encryption Coverage", max: 20, icon: Lock },
  { key: "consent_management", label: "Consent Coverage", max: 25, icon: ShieldCheck },
  { key: "audit_logging", label: "Audit Coverage", max: 20, icon: ClipboardList },
  { key: "blockchain_anchoring", label: "Blockchain Coverage", max: 20, icon: Link2 },
  { key: "dpdp_rights", label: "DPDP Rights Coverage", max: 15, icon: Scale },
];

export function ComplianceDashboard() {
  const { data: score } = useQuery({
    queryKey: ["compliance-score"],
    queryFn: complianceService.getScore,
  });

  const radarData = score
    ? CATEGORIES.map((c) => ({
        category: c.label.replace(" Coverage", ""),
        value: Math.round((score.breakdown[c.key] / c.max) * 100),
      }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-800">Compliance Breakdown</h1>
        <p className="mt-1 text-sm text-neutral-500">
          DPDP Act compliance scoring across all control areas
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Overall gauge */}
        <Card>
          <CardHeader>
            <CardTitle>Overall Score</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-center py-6">
            {score && <ComplianceGauge score={score.overall_score} grade={score.grade} />}
          </CardContent>
        </Card>

        {/* Radar chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Control Coverage</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#E5E7EB" />
                <PolarAngleAxis dataKey="category" tick={{ fontSize: 11, fill: "#6B7280" }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#9CA3AF" }} />
                <Radar
                  name="Coverage"
                  dataKey="value"
                  stroke="#2563EB"
                  fill="#2563EB"
                  fillOpacity={0.25}
                />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Category breakdown */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {score &&
          CATEGORIES.map((cat, i) => {
            const value = score.breakdown[cat.key];
            const pct = Math.round((value / cat.max) * 100);
            const Icon = cat.icon;
            const isHealthy = pct >= 70;

            return (
              <motion.div
                key={cat.key}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card>
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50">
                          <Icon className="h-4 w-4 text-primary-600" />
                        </div>
                        <span className="text-sm font-medium text-neutral-700">{cat.label}</span>
                      </div>
                      {isHealthy ? (
                        <CheckCircle2 className="h-5 w-5 text-success" />
                      ) : (
                        <AlertTriangle className="h-5 w-5 text-warning" />
                      )}
                    </div>

                    <div className="mt-4">
                      <div className="flex items-baseline justify-between">
                        <span className="text-2xl font-bold text-neutral-800">
                          {value}/{cat.max}
                        </span>
                        <Badge variant={isHealthy ? "success" : "warning"}>{pct}%</Badge>
                      </div>
                      <div className="mt-2 h-2 overflow-hidden rounded-full bg-neutral-100">
                        <motion.div
                          className={`h-full rounded-full ${isHealthy ? "bg-success" : "bg-warning"}`}
                          initial={{ width: 0 }}
                          animate={{ width: `${pct}%` }}
                          transition={{ duration: 0.8, delay: i * 0.05 }}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
      </div>

      {/* Risk indicators */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-warning" />
            Risk Indicators
          </CardTitle>
        </CardHeader>
        <CardContent>
          {score && (
            <div className="space-y-2">
              {CATEGORIES.filter((c) => score.breakdown[c.key] / c.max < 0.7).length === 0 ? (
                <div className="flex items-center gap-2 rounded-md bg-success/5 px-4 py-3 text-sm text-success">
                  <CheckCircle2 className="h-4 w-4" />
                  All control areas are within acceptable compliance thresholds.
                </div>
              ) : (
                CATEGORIES.filter((c) => score.breakdown[c.key] / c.max < 0.7).map((c) => (
                  <div
                    key={c.key}
                    className="flex items-center gap-2 rounded-md bg-warning/10 px-4 py-3 text-sm text-warning"
                  >
                    <AlertTriangle className="h-4 w-4" />
                    {c.label} is below the 70% threshold — review recommended.
                  </div>
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

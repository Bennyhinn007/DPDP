/**
 * DPO Dashboard.
 *
 * Compliance oversight with score gauge, metrics, and analytics charts.
 */

import { useQuery } from "@tanstack/react-query";
import {
  Users,
  FileText,
  ShieldCheck,
  Link2,
  Pencil,
  Trash2,
  Activity,
  Database,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { complianceService } from "@/services/complianceService";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { StatCard } from "@/components/shared/StatCard";
import { ComplianceGauge } from "@/components/shared/ComplianceGauge";

const BAR_COLORS = ["#2563EB", "#10B981", "#F59E0B", "#0F4C81", "#8B5CF6"];

export function DPODashboard() {
  const { data: stats } = useQuery({
    queryKey: ["compliance-stats"],
    queryFn: complianceService.getStats,
  });

  const { data: score } = useQuery({
    queryKey: ["compliance-score"],
    queryFn: complianceService.getScore,
  });

  const activityData = stats
    ? [
        { name: "Records", value: stats.total_records },
        { name: "Consents", value: stats.total_consents },
        { name: "Corrections", value: stats.total_corrections },
        { name: "Erasures", value: stats.total_erasures },
        { name: "Anchors", value: stats.total_blockchain_anchors },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-neutral-800">DPO Compliance Dashboard</h1>
        <p className="mt-1 text-sm text-neutral-500">
          System-wide data protection oversight
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Compliance score gauge */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Compliance Score</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-center py-6">
            {score && <ComplianceGauge score={score.overall_score} grade={score.grade} />}
          </CardContent>
        </Card>

        {/* Activity chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>System Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#6B7280" }} />
                <YAxis tick={{ fontSize: 12, fill: "#6B7280" }} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {activityData.map((_, i) => (
                    <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Patients" value={stats?.total_patients ?? 0} icon={Users} variant="primary" />
        <StatCard label="Health Records" value={stats?.total_records ?? 0} icon={FileText} variant="secondary" />
        <StatCard label="Active Consents" value={stats?.active_consents ?? 0} icon={ShieldCheck} variant="success" />
        <StatCard label="Blockchain Anchors" value={stats?.total_blockchain_anchors ?? 0} icon={Link2} variant="warning" />
        <StatCard label="Corrections" value={stats?.total_corrections ?? 0} icon={Pencil} variant="primary" />
        <StatCard label="Erasures" value={stats?.total_erasures ?? 0} icon={Trash2} variant="warning" />
        <StatCard label="Audit Events" value={stats?.total_audit_events ?? 0} icon={Activity} variant="secondary" />
        <StatCard label="Total Users" value={stats?.total_users ?? 0} icon={Database} variant="success" />
      </div>
    </div>
  );
}

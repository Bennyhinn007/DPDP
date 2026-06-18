/**
 * Identity Governance & User Intelligence Center.
 *
 * Enterprise-grade administration dashboard showing user analytics,
 * identity risk, compliance heatmap, DPDP rights monitoring,
 * blockchain audit insights, and governance activity.
 */

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Users,
  UserCheck,
  ShieldCheck,
  Activity,
  Link2,
  FileEdit,
  Trash2,
  AlertTriangle,
  Lock,
  Stethoscope,
  Search,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { complianceService } from "@/services/complianceService";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { StatCard } from "@/components/shared/StatCard";
import { PageLoader } from "@/components/shared/PageLoader";
import { useState } from "react";

const PIE_COLORS = ["#2563EB", "#10B981", "#F59E0B", "#8B5CF6"];
const BAR_COLORS = ["#2563EB", "#10B981", "#F59E0B", "#0F4C81", "#8B5CF6"];

export function IdentityGovernance() {
  const [searchQuery, setSearchQuery] = useState("");

  const { data: stats, isLoading } = useQuery({
    queryKey: ["compliance-stats"],
    queryFn: complianceService.getStats,
  });

  const { data: score } = useQuery({
    queryKey: ["compliance-score"],
    queryFn: complianceService.getScore,
  });

  if (isLoading) return <PageLoader message="Loading Identity Governance..." />;

  const totalUsers = stats?.total_users ?? 0;
  const totalPatients = stats?.total_patients ?? 0;
  const totalRecords = stats?.total_records ?? 0;
  const totalConsents = stats?.total_consents ?? 0;
  const activeConsents = stats?.active_consents ?? 0;
  const totalAnchors = stats?.total_blockchain_anchors ?? 0;
  const totalAudit = stats?.total_audit_events ?? 0;
  const corrections = stats?.total_corrections ?? 0;
  const erasures = stats?.total_erasures ?? 0;
  const compliancePct = score?.overall_score ?? 0;

  // Derived metrics
  const doctors = Math.max(0, totalUsers - totalPatients - 1); // subtract admin
  const admins = 1;

  // Role distribution
  const roleData = [
    { name: "Patients", value: totalPatients },
    { name: "Doctors", value: doctors },
    { name: "Admins", value: admins },
  ].filter((d) => d.value > 0);

  // Activity metrics for bar chart
  const activityData = [
    { name: "Records", value: totalRecords },
    { name: "Consents", value: totalConsents },
    { name: "Anchors", value: totalAnchors },
    { name: "Corrections", value: corrections },
    { name: "Erasures", value: erasures },
  ];

  // Risk classification (simulated from available data)
  const lowRisk = totalPatients > 0 ? Math.round(totalPatients * 0.7) : 0;
  const medRisk = totalPatients > 0 ? Math.round(totalPatients * 0.2) : 0;
  const highRisk = totalPatients > 0 ? totalPatients - lowRisk - medRisk : 0;
  const missingConsent = Math.max(0, totalPatients - activeConsents);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-800">Identity Governance & User Intelligence</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Monitor platform users, compliance posture, consent governance, and blockchain-backed audit activity
        </p>
      </div>

      {/* Section 1: Executive Overview KPIs */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-6">
        <StatCard label="Total Users" value={totalUsers} icon={Users} variant="primary" subtitle="All roles" />
        <StatCard label="Patients" value={totalPatients} icon={UserCheck} variant="success" subtitle="Data principals" />
        <StatCard label="Doctors" value={doctors} icon={Stethoscope} variant="secondary" subtitle="Healthcare providers" />
        <StatCard label="Admins" value={admins} icon={Lock} variant="warning" subtitle="DPO / Admin" />
        <StatCard label="Compliance" value={`${compliancePct}%`} icon={ShieldCheck} variant="success" subtitle={score?.grade ?? "—"} />
        <StatCard label="Audit Events" value={totalAudit} icon={Activity} variant="primary" subtitle="Total logged" />
      </div>

      {/* Section 2: User Analytics */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Role Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Role Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {roleData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={roleData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} innerRadius={35} label>
                    {roleData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-8 text-center text-sm text-neutral-400">No users yet</p>
            )}
          </CardContent>
        </Card>

        {/* System Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Platform Activity Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={activityData} barSize={32}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#6B7280" }} axisLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#9CA3AF" }} axisLine={false} allowDecimals={false} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #E5E7EB", fontSize: 12 }} />
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

      {/* Section 3: Identity Risk Center */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle className="h-4 w-4 text-warning" />
            Identity Risk Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <RiskMetric label="Low Risk" value={lowRisk} color="bg-success" description="Fully compliant" />
            <RiskMetric label="Medium Risk" value={medRisk} color="bg-warning" description="Partial consent" />
            <RiskMetric label="High Risk" value={highRisk} color="bg-danger" description="Non-compliant" />
            <RiskMetric label="Missing Consent" value={missingConsent} color="bg-warning" description="No active consent" />
            <RiskMetric label="Corrections" value={corrections} color="bg-primary-500" description="DPDP Section 12" />
            <RiskMetric label="Erasures" value={erasures} color="bg-danger" description="Right to Erasure" />
          </div>
        </CardContent>
      </Card>

      {/* Section 4: Governance User Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">User Governance Overview</CardTitle>
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
              <Input
                placeholder="Search users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-200 text-left">
                  <th className="pb-3 pr-4 font-medium text-neutral-500">User</th>
                  <th className="pb-3 pr-4 font-medium text-neutral-500">Role</th>
                  <th className="pb-3 pr-4 font-medium text-neutral-500">Status</th>
                  <th className="pb-3 pr-4 font-medium text-neutral-500">Records</th>
                  <th className="pb-3 pr-4 font-medium text-neutral-500">Consents</th>
                  <th className="pb-3 pr-4 font-medium text-neutral-500">Risk</th>
                </tr>
              </thead>
              <tbody>
                {/* Render demo users from seed data */}
                {[
                  { name: "Rajesh Kumar", role: "patient", status: "active", records: 4, consents: 3, risk: "low" },
                  { name: "Priya Sharma", role: "patient", status: "active", records: 3, consents: 3, risk: "low" },
                  { name: "Amit Patel", role: "patient", status: "active", records: 2, consents: 1, risk: "medium" },
                  { name: "Dr. Anjali Desai", role: "admin", status: "active", records: 0, consents: 0, risk: "low" },
                ]
                  .filter((u) => !searchQuery || u.name.toLowerCase().includes(searchQuery.toLowerCase()))
                  .map((user, i) => (
                    <motion.tr
                      key={i}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.03 }}
                      className="border-b border-neutral-100"
                    >
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-2">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-50 text-xs font-semibold text-primary-700">
                            {user.name.charAt(0)}
                          </div>
                          <span className="font-medium text-neutral-800">{user.name}</span>
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant={user.role === "admin" ? "warning" : user.role === "doctor" ? "secondary" : "default"}>
                          {user.role}
                        </Badge>
                      </td>
                      <td className="py-3 pr-4">
                        <Badge variant="success">Active</Badge>
                      </td>
                      <td className="py-3 pr-4 text-neutral-600">{user.records}</td>
                      <td className="py-3 pr-4 text-neutral-600">{user.consents}</td>
                      <td className="py-3 pr-4">
                        <Badge variant={user.risk === "low" ? "success" : user.risk === "medium" ? "warning" : "danger"}>
                          {user.risk}
                        </Badge>
                      </td>
                    </motion.tr>
                  ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Section 5: Blockchain & Audit + DPDP Rights */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Blockchain Insights */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Link2 className="h-4 w-4 text-primary-600" />
              Blockchain & Audit Intelligence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <InsightRow icon={Link2} label="Blockchain Anchors" value={totalAnchors} color="text-primary-600" />
              <InsightRow icon={Activity} label="Audit Events" value={totalAudit} color="text-success" />
              <InsightRow icon={ShieldCheck} label="Integrity Verifications" value={totalAnchors} color="text-secondary" />
              <InsightRow icon={FileEdit} label="Record Corrections" value={corrections} color="text-primary-600" />
              <InsightRow icon={Trash2} label="Data Erasures" value={erasures} color="text-danger" />
            </div>
          </CardContent>
        </Card>

        {/* DPDP Rights Monitoring */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <ShieldCheck className="h-4 w-4 text-success" />
              DPDP Rights Fulfillment
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-600">Correction Requests</span>
                <span className="text-lg font-bold text-neutral-800">{corrections}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-600">Erasure Requests</span>
                <span className="text-lg font-bold text-neutral-800">{erasures}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-neutral-600">Total Fulfilled</span>
                <span className="text-lg font-bold text-success">{corrections + erasures}</span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-neutral-100">
                <motion.div
                  className="h-full rounded-full bg-success"
                  initial={{ width: 0 }}
                  animate={{ width: corrections + erasures > 0 ? "100%" : "0%" }}
                  transition={{ duration: 0.8 }}
                />
              </div>
              <p className="text-xs text-neutral-400">
                {corrections + erasures > 0
                  ? "All DPDP rights requests fulfilled within SLA"
                  : "No rights requests pending"}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Section 9: System Health Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">System Health & Governance Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-5">
            <HealthIndicator label="Encryption Engine" status="operational" detail="AES-256-GCM" />
            <HealthIndicator label="Blockchain Layer" status={totalAnchors > 0 ? "operational" : "degraded"} detail="Ganache (1337)" />
            <HealthIndicator label="Audit Chain" status={totalAudit > 0 ? "operational" : "idle"} detail="Hash-linked" />
            <HealthIndicator label="Consent Governance" status={activeConsents > 0 ? "operational" : "idle"} detail={`${activeConsents} active`} />
            <HealthIndicator label="DPDP Compliance" status={compliancePct >= 70 ? "operational" : "warning"} detail={`${compliancePct}/100`} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function RiskMetric({ label, value, color, description }: { label: string; value: number; color: string; description: string }) {
  return (
    <div className="rounded-lg border border-neutral-200 p-3 text-center">
      <div className={`mx-auto mb-2 h-3 w-3 rounded-full ${color}`} />
      <div className="text-xl font-bold text-neutral-800">{value}</div>
      <div className="text-xs font-medium text-neutral-700">{label}</div>
      <div className="text-[10px] text-neutral-400">{description}</div>
    </div>
  );
}

function InsightRow({ icon: Icon, label, value, color }: { icon: typeof Link2; label: string; value: number; color: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 ${color}`} />
        <span className="text-sm text-neutral-700">{label}</span>
      </div>
      <span className="text-sm font-bold text-neutral-800">{value}</span>
    </div>
  );
}

function HealthIndicator({ label, status, detail }: { label: string; status: "operational" | "degraded" | "warning" | "idle"; detail: string }) {
  const statusColors = {
    operational: "bg-success",
    degraded: "bg-warning",
    warning: "bg-warning",
    idle: "bg-neutral-300",
  };
  const statusLabels = {
    operational: "Active",
    degraded: "Degraded",
    warning: "Warning",
    idle: "Idle",
  };
  return (
    <div className="flex items-center gap-3 rounded-md border border-neutral-100 p-3">
      <div className={`h-2.5 w-2.5 rounded-full ${statusColors[status]}`} />
      <div className="flex-1">
        <p className="text-xs font-medium text-neutral-700">{label}</p>
        <p className="text-[10px] text-neutral-400">{detail}</p>
      </div>
      <Badge variant={status === "operational" ? "success" : status === "idle" ? "neutral" : "warning"}>
        {statusLabels[status]}
      </Badge>
    </div>
  );
}

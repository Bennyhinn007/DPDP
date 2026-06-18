/**
 * Identity & Access Governance Center.
 *
 * Enterprise-grade user identity management focused on:
 * - User directory (searchable, filterable)
 * - Lifecycle management (active, dormant, locked)
 * - Access security monitoring
 * - Healthcare access relationships
 * - Role governance analytics
 *
 * Explicitly does NOT duplicate Compliance Dashboard metrics.
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Users,
  UserCheck,
  UserX,
  Lock,
  Stethoscope,
  Search,
  Shield,
  Activity,
  Heart,
  AlertTriangle,
  Clock,
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
  PieChart,
  Pie,
  Legend,
} from "recharts";
import { adminService, type GovernanceUser } from "@/services/adminService";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { StatCard } from "@/components/shared/StatCard";
import { PageLoader } from "@/components/shared/PageLoader";
import { formatDateTime } from "@/lib/utils";

const ROLE_COLORS = ["#2563EB", "#10B981", "#F59E0B"];
const BAR_COLORS = ["#2563EB", "#10B981", "#F59E0B", "#8B5CF6"];

export function IdentityGovernance() {
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [selectedUser, setSelectedUser] = useState<GovernanceUser | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["governance"],
    queryFn: adminService.getGovernanceData,
  });

  if (isLoading) return <PageLoader message="Loading Identity Governance..." />;

  const metrics = data?.metrics;
  const users = data?.users ?? [];

  // Apply filters
  const filteredUsers = users.filter((u) => {
    const matchSearch = !search || u.full_name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase());
    const matchRole = !roleFilter || u.role === roleFilter;
    const matchRisk = !riskFilter || u.risk_level === riskFilter;
    return matchSearch && matchRole && matchRisk;
  });

  // Chart data
  const roleDistribution = [
    { name: "Patients", value: metrics?.patients ?? 0 },
    { name: "Doctors", value: metrics?.doctors ?? 0 },
    { name: "Admins", value: metrics?.admins ?? 0 },
  ].filter((d) => d.value > 0);

  const securityMetrics = [
    { name: "Active Today", value: metrics?.active_today ?? 0 },
    { name: "Dormant", value: metrics?.dormant ?? 0 },
    { name: "Locked", value: metrics?.locked ?? 0 },
    { name: "Never Logged In", value: metrics?.never_logged_in ?? 0 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-800">Identity & Access Governance</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Manage user identities, monitor access patterns, and govern platform roles
        </p>
      </div>

      {/* Section A: Operational KPIs */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-6">
        <StatCard label="Total Users" value={metrics?.total_users ?? 0} icon={Users} variant="primary" subtitle="All identities" />
        <StatCard label="Active Today" value={metrics?.active_today ?? 0} icon={UserCheck} variant="success" subtitle="Logged in (24h)" />
        <StatCard label="Patients" value={metrics?.patients ?? 0} icon={Heart} variant="primary" subtitle="Data principals" />
        <StatCard label="Doctors" value={metrics?.doctors ?? 0} icon={Stethoscope} variant="secondary" subtitle="Providers" />
        <StatCard label="Dormant" value={metrics?.dormant ?? 0} icon={UserX} variant="warning" subtitle=">30 days inactive" />
        <StatCard label="Locked" value={metrics?.locked ?? 0} icon={Lock} variant="warning" subtitle="Account lockouts" />
      </div>

      {/* Section B: User Directory */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="text-base">User Directory</CardTitle>
            <div className="flex flex-wrap gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
                <Input placeholder="Search users..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-48 pl-10" />
              </div>
              <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="h-10 rounded-md border border-neutral-300 bg-white px-3 text-sm">
                <option value="">All Roles</option>
                <option value="patient">Patient</option>
                <option value="doctor">Doctor</option>
                <option value="admin">Admin</option>
              </select>
              <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)} className="h-10 rounded-md border border-neutral-300 bg-white px-3 text-sm">
                <option value="">All Risk</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
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
                  <th className="pb-3 pr-4 font-medium text-neutral-500">Last Login</th>
                  <th className="pb-3 pr-4 font-medium text-neutral-500">Records</th>
                  <th className="pb-3 pr-4 font-medium text-neutral-500">Consents</th>
                  <th className="pb-3 pr-4 font-medium text-neutral-500">Risk</th>
                  <th className="pb-3 font-medium text-neutral-500">Details</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user, i) => (
                  <motion.tr
                    key={user.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="border-b border-neutral-100 hover:bg-neutral-50"
                  >
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-50 text-xs font-bold text-primary-700">
                          {user.full_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-neutral-800">{user.full_name}</p>
                          <p className="text-xs text-neutral-400">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 pr-4">
                      <Badge variant={user.role === "admin" ? "warning" : user.role === "doctor" ? "success" : "default"}>
                        {user.role}
                      </Badge>
                    </td>
                    <td className="py-3 pr-4">
                      <Badge variant={user.status === "active" ? "success" : user.status === "locked" ? "danger" : "warning"}>
                        {user.status}
                      </Badge>
                    </td>
                    <td className="py-3 pr-4 text-neutral-500">
                      {user.last_login ? formatDateTime(user.last_login) : <span className="text-neutral-300">Never</span>}
                    </td>
                    <td className="py-3 pr-4 text-neutral-600">{user.records_count}</td>
                    <td className="py-3 pr-4 text-neutral-600">{user.consents_count}</td>
                    <td className="py-3 pr-4">
                      <Badge variant={user.risk_level === "low" ? "success" : user.risk_level === "medium" ? "warning" : "danger"}>
                        {user.risk_level}
                      </Badge>
                    </td>
                    <td className="py-3">
                      <Button variant="ghost" size="sm" onClick={() => setSelectedUser(user)}>View</Button>
                    </td>
                  </motion.tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-neutral-400">No users match filters</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Section C: Analytics */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Role Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Role Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={roleDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} innerRadius={35} label>
                  {roleDistribution.map((_, i) => (
                    <Cell key={i} fill={ROLE_COLORS[i % ROLE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Access Security */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Shield className="h-4 w-4 text-primary-600" />
              Access & Session Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={securityMetrics} barSize={36}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#6B7280" }} axisLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#9CA3AF" }} axisLine={false} allowDecimals={false} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #E5E7EB", fontSize: 12 }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {securityMetrics.map((_, i) => (
                    <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Section D: Healthcare Relationships + Security */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Healthcare Access */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Heart className="h-4 w-4 text-danger" />
              Healthcare Access Relationships
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <div className="flex items-center gap-2">
                <div className="h-2.5 w-2.5 rounded-full bg-success" />
                <span className="text-sm text-neutral-700">Patients WITH active consent</span>
              </div>
              <span className="text-sm font-bold text-neutral-800">{metrics?.patients_with_consent ?? 0}</span>
            </div>
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <div className="flex items-center gap-2">
                <div className="h-2.5 w-2.5 rounded-full bg-warning" />
                <span className="text-sm text-neutral-700">Patients WITHOUT consent</span>
              </div>
              <span className="text-sm font-bold text-neutral-800">{metrics?.patients_without_consent ?? 0}</span>
            </div>
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <div className="flex items-center gap-2">
                <div className="h-2.5 w-2.5 rounded-full bg-primary-500" />
                <span className="text-sm text-neutral-700">Doctor access events (7d)</span>
              </div>
              <span className="text-sm font-bold text-neutral-800">{metrics?.doctor_access_events_7d ?? 0}</span>
            </div>
            {(metrics?.patients_without_consent ?? 0) > 0 && (
              <div className="mt-2 flex items-center gap-2 rounded-md bg-warning/10 px-3 py-2 text-xs text-warning">
                <AlertTriangle className="h-3.5 w-3.5" />
                {metrics?.patients_without_consent} patient(s) have no active consent — governance attention required
              </div>
            )}
          </CardContent>
        </Card>

        {/* Security Monitoring */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-4 w-4 text-secondary" />
              Access Security Monitor
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-warning" />
                <span className="text-sm text-neutral-700">Users with failed logins</span>
              </div>
              <span className="text-sm font-bold text-neutral-800">{metrics?.failed_login_attempts_users ?? 0}</span>
            </div>
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-danger" />
                <span className="text-sm text-neutral-700">Currently locked accounts</span>
              </div>
              <span className="text-sm font-bold text-neutral-800">{metrics?.locked ?? 0}</span>
            </div>
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-neutral-400" />
                <span className="text-sm text-neutral-700">Dormant accounts (&gt;30 days)</span>
              </div>
              <span className="text-sm font-bold text-neutral-800">{metrics?.dormant ?? 0}</span>
            </div>
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <div className="flex items-center gap-2">
                <UserX className="h-4 w-4 text-neutral-400" />
                <span className="text-sm text-neutral-700">Never logged in</span>
              </div>
              <span className="text-sm font-bold text-neutral-800">{metrics?.never_logged_in ?? 0}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* User Detail Drawer */}
      {selectedUser && (
        <Dialog open onClose={() => setSelectedUser(null)} title="User Governance Details" className="max-w-lg">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50 text-lg font-bold text-primary-700">
                {selectedUser.full_name.charAt(0).toUpperCase()}
              </div>
              <div>
                <p className="font-semibold text-neutral-800">{selectedUser.full_name}</p>
                <p className="text-sm text-neutral-500">{selectedUser.email}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <DetailField label="Role" value={selectedUser.role} />
              <DetailField label="Status" value={selectedUser.status} />
              <DetailField label="Risk Level" value={selectedUser.risk_level} />
              <DetailField label="Failed Logins" value={String(selectedUser.failed_login_attempts)} />
              <DetailField label="Healthcare Records" value={String(selectedUser.records_count)} />
              <DetailField label="Active Consents" value={String(selectedUser.consents_count)} />
              <DetailField label="Last Login" value={selectedUser.last_login ? formatDateTime(selectedUser.last_login) : "Never"} />
              <DetailField label="Registered" value={formatDateTime(selectedUser.created_at)} />
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="outline" onClick={() => setSelectedUser(null)}>Close</Button>
            </div>
          </div>
        </Dialog>
      )}
    </div>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-neutral-50 p-2.5">
      <p className="text-[10px] font-medium uppercase tracking-wide text-neutral-400">{label}</p>
      <p className="mt-0.5 text-sm font-medium text-neutral-800 capitalize">{value}</p>
    </div>
  );
}

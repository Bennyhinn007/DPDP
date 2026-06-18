/**
 * User Profile Page.
 *
 * Universal profile view for all roles.
 * Shows identity details, security status, activity summary, and role-specific info.
 */

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  User,
  Mail,
  Shield,
  Clock,
  Lock,
  Activity,
  FileText,
  ShieldCheck,
  Fingerprint,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { patientService } from "@/services/patientService";
import { consentService } from "@/services/consentService";
import { auditService } from "@/services/auditService";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageLoader } from "@/components/shared/PageLoader";
import { formatDateTime, humanize } from "@/lib/utils";

export function ProfilePage() {
  const { user } = useAuth();

  // Patient-specific data
  const { isLoading: profileLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: patientService.getProfile,
    enabled: user?.role === "patient",
  });

  const { data: consents = [] } = useQuery({
    queryKey: ["consents"],
    queryFn: consentService.list,
    enabled: user?.role === "patient",
  });

  const { data: records = [] } = useQuery({
    queryKey: ["records"],
    queryFn: patientService.listRecords,
    enabled: user?.role === "patient",
  });

  const { data: timeline = [] } = useQuery({
    queryKey: ["timeline"],
    queryFn: () => auditService.getTimeline(),
    enabled: user?.role === "patient",
  });

  if (!user) return null;
  if (user.role === "patient" && profileLoading) return <PageLoader message="Loading profile..." />;

  const activeConsents = consents.filter((c) => c.status === "active").length;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-800">My Profile</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Identity details, security status, and account activity
        </p>
      </div>

      {/* Identity Card */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start gap-5">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 text-2xl font-bold text-primary-700">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-neutral-800">{user.full_name}</h2>
              <p className="text-sm text-neutral-500">{user.email}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <Badge variant={user.role === "admin" ? "warning" : user.role === "doctor" ? "success" : "default"}>
                  {humanize(user.role)}
                </Badge>
                <Badge variant="success">Active</Badge>
                {user.mfa_enabled && <Badge variant="neutral">MFA Enabled</Badge>}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Identity Details */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Fingerprint className="h-4 w-4 text-primary-600" />
              Identity Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <DetailRow icon={User} label="Full Name" value={user.full_name} />
            <DetailRow icon={Mail} label="Email" value={user.email} />
            <DetailRow icon={Shield} label="Role" value={humanize(user.role)} />
            <DetailRow icon={Clock} label="Last Login" value={user.last_login ? formatDateTime(user.last_login) : "Current session"} />
            <DetailRow icon={Clock} label="Registered" value={formatDateTime(user.created_at)} />
          </CardContent>
        </Card>

        {/* Security Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Lock className="h-4 w-4 text-success" />
              Security Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <span className="text-sm text-neutral-700">Account Status</span>
              <Badge variant="success">Active</Badge>
            </div>
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <span className="text-sm text-neutral-700">Authentication</span>
              <Badge variant="success">JWT (HS256)</Badge>
            </div>
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <span className="text-sm text-neutral-700">Encryption</span>
              <Badge variant="success">AES-256</Badge>
            </div>
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <span className="text-sm text-neutral-700">Data Residency</span>
              <Badge variant="neutral">India</Badge>
            </div>
            <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
              <span className="text-sm text-neutral-700">MFA</span>
              <Badge variant={user.mfa_enabled ? "success" : "neutral"}>
                {user.mfa_enabled ? "Enabled" : "Not configured"}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Patient-specific: Records + Consents + Activity */}
      {user.role === "patient" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="h-full">
              <CardContent className="flex flex-col items-center justify-center py-8 text-center">
                <FileText className="h-8 w-8 text-primary-600" />
                <div className="mt-3 text-3xl font-bold text-neutral-800">{records.length}</div>
                <p className="text-sm text-neutral-500">Healthcare Records</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
            <Card className="h-full">
              <CardContent className="flex flex-col items-center justify-center py-8 text-center">
                <ShieldCheck className="h-8 w-8 text-success" />
                <div className="mt-3 text-3xl font-bold text-neutral-800">{activeConsents}</div>
                <p className="text-sm text-neutral-500">Active Consents</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <Card className="h-full">
              <CardContent className="flex flex-col items-center justify-center py-8 text-center">
                <Activity className="h-8 w-8 text-warning" />
                <div className="mt-3 text-3xl font-bold text-neutral-800">{timeline.length}</div>
                <p className="text-sm text-neutral-500">Audit Events</p>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4 text-neutral-600" />
            Recent Account Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          {user.role === "patient" && timeline.length > 0 ? (
            <ul className="space-y-2">
              {timeline.slice(0, 5).map((event) => (
                <li key={event._id} className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-primary-400" />
                    <span className="text-sm text-neutral-700">{humanize(event.action_type)}</span>
                  </div>
                  <span className="text-xs text-neutral-400">{formatDateTime(event.created_at)}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="py-6 text-center text-sm text-neutral-400">
              {user.role !== "patient"
                ? "Admin activity tracked via DPO Dashboard audit logs"
                : "No recent activity recorded"}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DetailRow({ icon: Icon, label, value }: { icon: typeof User; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-neutral-100 px-3 py-2.5">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-neutral-400" />
        <span className="text-sm text-neutral-600">{label}</span>
      </div>
      <span className="text-sm font-medium text-neutral-800">{value}</span>
    </div>
  );
}

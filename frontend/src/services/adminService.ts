/**
 * Admin Governance API Service.
 */

import api from "./api";

export interface GovernanceUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
  status: string;
  last_login: string | null;
  failed_login_attempts: number;
  records_count: number;
  consents_count: number;
  risk_level: "low" | "medium" | "high";
  created_at: string;
}

export interface GovernanceMetrics {
  total_users: number;
  active_today: number;
  patients: number;
  doctors: number;
  admins: number;
  locked: number;
  dormant: number;
  never_logged_in: number;
  failed_login_attempts_users: number;
  patients_with_consent: number;
  patients_without_consent: number;
  doctor_access_events_7d: number;
}

export interface GovernanceData {
  metrics: GovernanceMetrics;
  users: GovernanceUser[];
  generated_at: string;
}

export const adminService = {
  async getGovernanceData(): Promise<GovernanceData> {
    const { data } = await api.get<{ governance: GovernanceData }>("/compliance/governance");
    return data.governance;
  },
};

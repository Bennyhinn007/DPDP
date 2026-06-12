/**
 * Compliance Dashboard API Service.
 */

import api from "./api";
import type { ComplianceScore } from "@/types";

export interface ComplianceStats {
  total_users: number;
  total_patients: number;
  total_records: number;
  total_consents: number;
  active_consents: number;
  withdrawn_consents: number;
  total_audit_events: number;
  total_blockchain_anchors: number;
  total_corrections: number;
  total_erasures: number;
  redacted_records: number;
}

export const complianceService = {
  async getStats(): Promise<ComplianceStats> {
    const { data } = await api.get<{ stats: ComplianceStats }>("/compliance/stats");
    return data.stats;
  },

  async getScore(): Promise<ComplianceScore> {
    const { data } = await api.get<{ compliance_score: ComplianceScore }>(
      "/compliance/compliance-score"
    );
    return data.compliance_score;
  },

  async getDashboard(): Promise<Record<string, unknown>> {
    const { data } = await api.get<{ dashboard: Record<string, unknown> }>(
      "/compliance/dashboard"
    );
    return data.dashboard;
  },
};

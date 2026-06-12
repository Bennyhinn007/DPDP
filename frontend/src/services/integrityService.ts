/**
 * Integrity Verification API Service.
 */

import api from "./api";
import type { VerificationResult } from "@/types";

export const integrityService = {
  async verifyRecord(recordId: string): Promise<VerificationResult> {
    const { data } = await api.get<{ verification: VerificationResult }>(
      `/integrity/record/${recordId}`
    );
    return data.verification;
  },

  async getStatus(): Promise<{
    connected: boolean;
    block_number: number | null;
    total_anchors: number;
  }> {
    const { data } = await api.get<{
      blockchain: { connected: boolean; block_number: number | null; total_anchors: number };
    }>("/integrity/status");
    return data.blockchain;
  },
};

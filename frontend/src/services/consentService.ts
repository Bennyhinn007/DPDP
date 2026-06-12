/**
 * Consent API Service.
 */

import api from "./api";
import type { Consent, ConsentType } from "@/types";

export const consentService = {
  async list(): Promise<Consent[]> {
    const { data } = await api.get<{ consents: Consent[] }>("/consents/");
    return data.consents;
  },

  async grant(
    consentType: ConsentType,
    processingEntityName: string,
    expiryDays = 365
  ): Promise<Consent> {
    const { data } = await api.post<{ consent: Consent }>("/consents/grant", {
      consent_type: consentType,
      processing_entity_name: processingEntityName,
      expiry_days: expiryDays,
    });
    return data.consent;
  },

  async modify(consentId: string, newScope: string[], reason: string): Promise<Consent> {
    const { data } = await api.put<{ consent: Consent }>(`/consents/${consentId}/modify`, {
      new_scope: newScope,
      reason,
    });
    return data.consent;
  },

  async withdraw(consentId: string, reason: string): Promise<Consent> {
    const { data } = await api.post<{ consent: Consent }>(`/consents/${consentId}/withdraw`, {
      reason,
    });
    return data.consent;
  },
};

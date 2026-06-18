/**
 * MFA (Google Authenticator) API Service.
 */

import api from "./api";

export interface MFASetupResponse {
  secret: string;
  provisioning_uri: string;
  qr_code_base64: string;
  instructions: string;
}

export interface MFAVerifyResponse {
  message: string;
  mfa_enabled: boolean;
}

export const mfaService = {
  async setup(): Promise<MFASetupResponse> {
    const { data } = await api.post<MFASetupResponse>("/auth/mfa/setup");
    return data;
  },

  async verify(code: string): Promise<MFAVerifyResponse> {
    const { data } = await api.post<MFAVerifyResponse>("/auth/mfa/verify", { code });
    return data;
  },

  async disable(code: string): Promise<MFAVerifyResponse> {
    const { data } = await api.post<MFAVerifyResponse>("/auth/mfa/disable", { code });
    return data;
  },
};

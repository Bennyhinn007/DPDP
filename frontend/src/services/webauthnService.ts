/**
 * WebAuthn Biometric API Service.
 */

import api from "./api";

export interface WebAuthnCredential {
  id: string;
  credential_id: string;
  device_name: string;
  created_at: string;
  last_used: string | null;
}

export interface WebAuthnOptions {
  rp: { id: string; name: string };
  user: { id: string; name: string; displayName: string };
  challenge: string;
  pubKeyCredParams: Array<{ type: string; alg: number }>;
  timeout: number;
  authenticatorSelection: Record<string, string>;
  excludeCredentials: Array<{ id: string; type: string }>;
  attestation: string;
}

export const webauthnService = {
  async beginRegistration(): Promise<WebAuthnOptions> {
    const { data } = await api.post<{ options: WebAuthnOptions }>("/auth/webauthn/register/begin");
    return data.options;
  },

  async completeRegistration(credential: {
    credential_id: string;
    public_key: string;
    attestation_object: string;
    client_data_json: string;
    device_name: string;
  }) {
    const { data } = await api.post("/auth/webauthn/register/complete", credential);
    return data;
  },

  async listCredentials(): Promise<{ credentials: WebAuthnCredential[]; biometric_enabled: boolean }> {
    const { data } = await api.get<{ credentials: WebAuthnCredential[]; biometric_enabled: boolean }>(
      "/auth/webauthn/credentials"
    );
    return data;
  },

  async removeCredential(credId: string) {
    await api.delete(`/auth/webauthn/credentials/${credId}`);
  },
};

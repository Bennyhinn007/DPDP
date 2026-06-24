/**
 * Biometric Enrollment Panel.
 *
 * WebAuthn registration for Admin/DPO users.
 * Supports: Windows Hello, Fingerprint, Face Recognition.
 */

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Fingerprint, Trash2, ShieldCheck, AlertCircle, Plus } from "lucide-react";
import { webauthnService } from "@/services/webauthnService";
import { getErrorMessage } from "@/services/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/utils";

export function BiometricPanel() {
  const queryClient = useQueryClient();
  const [enrolling, setEnrolling] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const { data } = useQuery({
    queryKey: ["webauthn-credentials"],
    queryFn: webauthnService.listCredentials,
  });

  const credentials = data?.credentials ?? [];
  const biometricEnabled = data?.biometric_enabled ?? false;

  const handleEnroll = async () => {
    setEnrolling(true);
    setError("");
    setSuccess("");

    try {
      // Step 1: Get registration options from server
      const options = await webauthnService.beginRegistration();

      // Step 2: Call browser WebAuthn API
      const publicKeyOptions: PublicKeyCredentialCreationOptions = {
        rp: options.rp,
        user: {
          id: Uint8Array.from(atob(options.user.id.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0)),
          name: options.user.name,
          displayName: options.user.displayName,
        },
        challenge: Uint8Array.from(atob(options.challenge.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0)),
        pubKeyCredParams: options.pubKeyCredParams as PublicKeyCredentialParameters[],
        timeout: options.timeout,
        authenticatorSelection: {
          authenticatorAttachment: "platform" as AuthenticatorAttachment,
          userVerification: "required" as UserVerificationRequirement,
        },
        attestation: "none" as AttestationConveyancePreference,
      };

      const credential = await navigator.credentials.create({
        publicKey: publicKeyOptions,
      }) as PublicKeyCredential;

      if (!credential) {
        setError("Biometric registration cancelled");
        return;
      }

      const response = credential.response as AuthenticatorAttestationResponse;

      // Step 3: Send to server
      const credId = btoa(String.fromCharCode(...new Uint8Array(credential.rawId))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
      const clientDataJSON = btoa(String.fromCharCode(...new Uint8Array(response.clientDataJSON))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
      const attestationObject = btoa(String.fromCharCode(...new Uint8Array(response.attestationObject))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");

      await webauthnService.completeRegistration({
        credential_id: credId,
        public_key: credId, // Simplified for demo
        attestation_object: attestationObject,
        client_data_json: clientDataJSON,
        device_name: detectDeviceName(),
      });

      setSuccess("Biometric enrolled successfully!");
      queryClient.invalidateQueries({ queryKey: ["webauthn-credentials"] });
    } catch (err) {
      const msg = getErrorMessage(err);
      if (msg.includes("NotAllowedError") || msg.includes("cancelled")) {
        setError("Registration cancelled by user");
      } else {
        setError(msg || "Biometric enrollment failed. Ensure your device supports Windows Hello or fingerprint.");
      }
    } finally {
      setEnrolling(false);
    }
  };

  const handleRemove = async (credId: string) => {
    try {
      await webauthnService.removeCredential(credId);
      queryClient.invalidateQueries({ queryKey: ["webauthn-credentials"] });
      setSuccess("Credential removed");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Fingerprint className="h-4 w-4 text-primary-600" />
          Biometric Authentication
          {biometricEnabled ? (
            <Badge variant="success">Active</Badge>
          ) : (
            <Badge variant="neutral">Not Configured</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-neutral-600">
          Register Windows Hello, fingerprint, or face recognition for passwordless authentication.
          No biometric data leaves your device — only public keys are stored.
        </p>

        {error && (
          <div className="flex items-center gap-2 rounded-md bg-danger/5 px-3 py-2 text-sm text-danger">
            <AlertCircle className="h-4 w-4" /> {error}
          </div>
        )}

        {success && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="flex items-center gap-2 rounded-md bg-success/10 px-3 py-2 text-sm text-success">
            <ShieldCheck className="h-4 w-4" /> {success}
          </motion.div>
        )}

        {/* Registered credentials */}
        {credentials.length > 0 && (
          <div className="space-y-2">
            {credentials.map((cred) => (
              <div key={cred.id} className="flex items-center justify-between rounded-md border border-neutral-200 px-3 py-2.5">
                <div className="flex items-center gap-2">
                  <Fingerprint className="h-4 w-4 text-success" />
                  <div>
                    <p className="text-sm font-medium text-neutral-700">{cred.device_name}</p>
                    <p className="text-xs text-neutral-400">
                      Registered {formatDateTime(cred.created_at)}
                      {cred.last_used && ` · Last used ${formatDateTime(cred.last_used)}`}
                    </p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => handleRemove(cred.id)}>
                  <Trash2 className="h-3.5 w-3.5 text-danger" />
                </Button>
              </div>
            ))}
          </div>
        )}

        <Button onClick={handleEnroll} disabled={enrolling}>
          <Plus className="h-4 w-4" />
          {enrolling ? "Authenticating..." : "Register Biometric"}
        </Button>

        <p className="text-[10px] text-neutral-400">
          DPDP Compliant: No biometric templates stored server-side. Only FIDO2 public keys retained.
        </p>
      </CardContent>
    </Card>
  );
}

function detectDeviceName(): string {
  const ua = navigator.userAgent;
  if (ua.includes("Windows")) return "Windows Hello";
  if (ua.includes("Mac")) return "Touch ID";
  if (ua.includes("Android")) return "Android Biometric";
  return "Platform Authenticator";
}

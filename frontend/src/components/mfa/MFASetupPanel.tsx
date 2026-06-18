/**
 * MFA Setup Panel.
 *
 * Complete Google Authenticator setup flow:
 * 1. Generate QR code
 * 2. Display scan instructions
 * 3. Show backup secret key
 * 4. Verify with 6-digit code
 * 5. Confirm enablement
 */

import { useState } from "react";
import { motion } from "framer-motion";
import { Key, ShieldCheck, Copy, CheckCircle2, AlertCircle, Smartphone } from "lucide-react";
import { mfaService, type MFASetupResponse } from "@/services/mfaService";
import { getErrorMessage } from "@/services/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";

interface MFASetupPanelProps {
  mfaEnabled: boolean;
  onMFAChange: () => void;
}

export function MFASetupPanel({ mfaEnabled, onMFAChange }: MFASetupPanelProps) {
  const [setupData, setSetupData] = useState<MFASetupResponse | null>(null);
  const [setupLoading, setSetupLoading] = useState(false);
  const [verifyCode, setVerifyCode] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showDisable, setShowDisable] = useState(false);
  const [disableCode, setDisableCode] = useState("");
  const [disabling, setDisabling] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleSetup = async () => {
    setSetupLoading(true);
    setError("");
    try {
      const data = await mfaService.setup();
      setSetupData(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSetupLoading(false);
    }
  };

  const handleVerify = async () => {
    if (verifyCode.length !== 6) {
      setError("Enter a 6-digit code");
      return;
    }
    setVerifying(true);
    setError("");
    try {
      await mfaService.verify(verifyCode);
      setSuccess("MFA enabled successfully! Your account is now protected with Google Authenticator.");
      setSetupData(null);
      setVerifyCode("");
      onMFAChange();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setVerifying(false);
    }
  };

  const handleDisable = async () => {
    if (disableCode.length !== 6) {
      setError("Enter a 6-digit code to disable MFA");
      return;
    }
    setDisabling(true);
    setError("");
    try {
      await mfaService.disable(disableCode);
      setSuccess("MFA disabled. Your account no longer requires two-factor authentication.");
      setShowDisable(false);
      setDisableCode("");
      onMFAChange();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDisabling(false);
    }
  };

  const copySecret = () => {
    if (setupData) {
      navigator.clipboard.writeText(setupData.secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // MFA is enabled — show status and disable option
  if (mfaEnabled && !success) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Key className="h-4 w-4 text-success" />
            Two-Factor Authentication
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-success/10">
                <ShieldCheck className="h-5 w-5 text-success" />
              </div>
              <div>
                <p className="text-sm font-medium text-neutral-800">Google Authenticator</p>
                <p className="text-xs text-neutral-500">TOTP-based two-factor authentication active</p>
              </div>
            </div>
            <Badge variant="success">Enabled</Badge>
          </div>

          {error && (
            <div className="mt-3 flex items-center gap-2 rounded-md bg-danger/5 px-3 py-2 text-sm text-danger">
              <AlertCircle className="h-4 w-4" /> {error}
            </div>
          )}

          <Button variant="outline" size="sm" className="mt-4" onClick={() => setShowDisable(true)}>
            Disable MFA
          </Button>

          {/* Disable dialog */}
          {showDisable && (
            <Dialog open onClose={() => setShowDisable(false)} title="Disable Two-Factor Authentication" description="Enter your current authenticator code to confirm">
              <div className="space-y-4">
                <div className="rounded-md bg-warning/10 px-3 py-2 text-sm text-warning">
                  Disabling MFA will reduce your account security. This action is audited.
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="disable-code">Authenticator Code</Label>
                  <Input
                    id="disable-code"
                    value={disableCode}
                    onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    placeholder="000000"
                    maxLength={6}
                    className="text-center font-mono text-lg tracking-widest"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setShowDisable(false)}>Cancel</Button>
                  <Button variant="danger" onClick={handleDisable} disabled={disabling || disableCode.length !== 6}>
                    {disabling ? "Disabling..." : "Disable MFA"}
                  </Button>
                </div>
              </div>
            </Dialog>
          )}
        </CardContent>
      </Card>
    );
  }

  // Success state
  if (success) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
            <CheckCircle2 className="mx-auto h-12 w-12 text-success" />
          </motion.div>
          <p className="mt-4 text-sm font-medium text-success">{success}</p>
        </CardContent>
      </Card>
    );
  }

  // Setup flow active — show QR code
  if (setupData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Smartphone className="h-4 w-4 text-primary-600" />
            Setup Google Authenticator
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Step 1: Scan */}
          <div>
            <p className="mb-2 text-sm font-medium text-neutral-700">Step 1: Scan this QR code</p>
            <p className="mb-3 text-xs text-neutral-500">
              Open Google Authenticator on your phone → tap + → Scan QR code
            </p>
            <div className="flex justify-center rounded-lg border border-neutral-200 bg-white p-4">
              {setupData.qr_code_base64 ? (
                <img
                  src={`data:image/png;base64,${setupData.qr_code_base64}`}
                  alt="MFA QR Code"
                  className="h-48 w-48"
                />
              ) : (
                <div className="flex h-48 w-48 items-center justify-center bg-neutral-50 text-xs text-neutral-400">
                  QR generation requires qrcode library
                </div>
              )}
            </div>
          </div>

          {/* Step 2: Backup key */}
          <div>
            <p className="mb-2 text-sm font-medium text-neutral-700">Step 2: Save backup key</p>
            <p className="mb-2 text-xs text-neutral-500">
              Store this key securely. You&apos;ll need it if you lose your phone.
            </p>
            <div className="flex items-center gap-2 rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2">
              <code className="flex-1 font-mono text-sm text-neutral-800 tracking-wider">{setupData.secret}</code>
              <button onClick={copySecret} className="rounded p-1 text-neutral-400 hover:text-neutral-600" aria-label="Copy">
                {copied ? <CheckCircle2 className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* Step 3: Verify */}
          <div>
            <p className="mb-2 text-sm font-medium text-neutral-700">Step 3: Enter verification code</p>
            <p className="mb-2 text-xs text-neutral-500">
              Enter the 6-digit code shown in your authenticator app
            </p>

            {error && (
              <div className="mb-2 flex items-center gap-2 rounded-md bg-danger/5 px-3 py-2 text-sm text-danger">
                <AlertCircle className="h-4 w-4" /> {error}
              </div>
            )}

            <div className="flex gap-2">
              <Input
                value={verifyCode}
                onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="000000"
                maxLength={6}
                className="text-center font-mono text-lg tracking-widest"
              />
              <Button onClick={handleVerify} disabled={verifying || verifyCode.length !== 6}>
                {verifying ? "Verifying..." : "Verify & Enable"}
              </Button>
            </div>
          </div>

          <Button variant="outline" onClick={() => setSetupData(null)} className="w-full">
            Cancel Setup
          </Button>
        </CardContent>
      </Card>
    );
  }

  // Default: MFA not enabled, show enable button
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Key className="h-4 w-4 text-neutral-500" />
          Two-Factor Authentication
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-neutral-700">Protect your account with Google Authenticator</p>
            <p className="text-xs text-neutral-400">Adds a 6-digit code requirement after password entry</p>
          </div>
          <Badge variant="neutral">Not Configured</Badge>
        </div>

        {error && (
          <div className="mt-3 flex items-center gap-2 rounded-md bg-danger/5 px-3 py-2 text-sm text-danger">
            <AlertCircle className="h-4 w-4" /> {error}
          </div>
        )}

        <Button className="mt-4" onClick={handleSetup} disabled={setupLoading}>
          <Key className="h-4 w-4" />
          {setupLoading ? "Setting up..." : "Enable MFA"}
        </Button>
      </CardContent>
    </Card>
  );
}

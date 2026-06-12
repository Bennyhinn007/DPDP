/**
 * Integrity Verification.
 *
 * Verify healthcare records against blockchain anchors with visual status badges.
 */

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  Link2,
  Hash,
  Box,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { patientService } from "@/services/patientService";
import { integrityService } from "@/services/integrityService";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { truncateHash, formatDateTime, humanize } from "@/lib/utils";
import type { VerificationResult } from "@/types";

const STATUS_CONFIG: Record<
  VerificationResult["status"],
  { label: string; variant: "success" | "warning" | "danger" | "neutral"; icon: typeof ShieldCheck }
> = {
  VERIFIED: { label: "Verified", variant: "success", icon: ShieldCheck },
  VERIFIED_MODIFIED: { label: "Verified (Modified)", variant: "warning", icon: ShieldCheck },
  VERIFIED_REDACTED: { label: "Verified (Redacted)", variant: "warning", icon: ShieldCheck },
  INTEGRITY_VIOLATION: { label: "Integrity Violation", variant: "danger", icon: ShieldX },
  NO_ANCHOR: { label: "No Anchor", variant: "neutral", icon: ShieldAlert },
};

export function IntegrityVerification() {
  const [results, setResults] = useState<Record<string, VerificationResult>>({});

  const { data: records = [] } = useQuery({
    queryKey: ["records"],
    queryFn: patientService.listRecords,
  });

  const { data: status } = useQuery({
    queryKey: ["blockchain-status"],
    queryFn: integrityService.getStatus,
  });

  const verifyMutation = useMutation({
    mutationFn: (recordId: string) => integrityService.verifyRecord(recordId),
    onSuccess: (result) => {
      setResults((prev) => ({ ...prev, [result.record_id]: result }));
    },
  });

  const verifyAll = () => {
    records.forEach((r) => verifyMutation.mutate(r._id));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-800">Data Integrity Verification</h1>
          <p className="mt-1 text-sm text-neutral-500">
            Verify your records against blockchain-anchored hashes
          </p>
        </div>
        <Button onClick={verifyAll} disabled={records.length === 0}>
          <ShieldCheck className="h-4 w-4" />
          Verify All Records
        </Button>
      </div>

      {/* Blockchain status */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-6 p-4">
          <div className="flex items-center gap-2">
            <div className={`h-2.5 w-2.5 rounded-full ${status?.connected ? "bg-success" : "bg-danger"}`} />
            <span className="text-sm font-medium text-neutral-700">
              Ganache {status?.connected ? "Connected" : "Disconnected"}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-neutral-500">
            <Box className="h-4 w-4" />
            Block #{status?.block_number ?? "—"}
          </div>
          <div className="flex items-center gap-2 text-sm text-neutral-500">
            <Link2 className="h-4 w-4" />
            {status?.total_anchors ?? 0} total anchors
          </div>
        </CardContent>
      </Card>

      {/* Records to verify */}
      <div className="space-y-4">
        {records.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-sm text-neutral-400">
              No records to verify
            </CardContent>
          </Card>
        ) : (
          records.map((rec) => {
            const result = results[rec._id];
            return (
              <Card key={rec._id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">
                      {rec.title}
                      <span className="ml-2 text-xs font-normal text-neutral-400">
                        {humanize(rec.record_type)} · v{rec.version}
                      </span>
                    </CardTitle>
                    {result ? (
                      <StatusBadge status={result.status} />
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => verifyMutation.mutate(rec._id)}
                        disabled={verifyMutation.isPending}
                      >
                        Verify
                      </Button>
                    )}
                  </div>
                </CardHeader>
                {result && (
                  <CardContent>
                    <p className="mb-4 text-sm text-neutral-600">{result.message}</p>

                    {/* Hash comparison cards */}
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                      <HashCard
                        label="Current Hash"
                        value={result.current_hash}
                        icon={Hash}
                      />
                      <HashCard
                        label="Blockchain Hash"
                        value={result.blockchain_hash}
                        icon={Link2}
                      />
                      <HashCard
                        label="Transaction Hash"
                        value={result.transaction_hash}
                        icon={Hash}
                      />
                      <div className="rounded-lg border border-neutral-200 p-3">
                        <div className="flex items-center gap-2 text-xs font-medium text-neutral-500">
                          <Box className="h-3.5 w-3.5" />
                          Block Number
                        </div>
                        <p className="mt-1 font-mono text-sm text-neutral-800">
                          {result.block_number ?? "—"}
                        </p>
                      </div>
                    </div>

                    {/* Match indicator */}
                    <div className="mt-4 flex items-center gap-2 rounded-md bg-neutral-50 px-3 py-2">
                      {result.current_hash === result.blockchain_hash ? (
                        <>
                          <CheckCircle2 className="h-4 w-4 text-success" />
                          <span className="text-sm text-success">Hashes match — record intact</span>
                        </>
                      ) : result.status.startsWith("VERIFIED") ? (
                        <>
                          <CheckCircle2 className="h-4 w-4 text-warning" />
                          <span className="text-sm text-warning">
                            Authorized modification — chameleon proof valid
                          </span>
                        </>
                      ) : (
                        <>
                          <XCircle className="h-4 w-4 text-danger" />
                          <span className="text-sm text-danger">
                            Hash mismatch — possible tampering
                          </span>
                        </>
                      )}
                    </div>

                    {result.verified_at && (
                      <p className="mt-2 text-xs text-neutral-400">
                        Verified {formatDateTime(result.verified_at)}
                      </p>
                    )}
                  </CardContent>
                )}
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: VerificationResult["status"] }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      <Icon className="h-3.5 w-3.5" />
      {config.label}
    </Badge>
  );
}

function HashCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | undefined;
  icon: typeof Hash;
}) {
  return (
    <div className="rounded-lg border border-neutral-200 p-3">
      <div className="flex items-center gap-2 text-xs font-medium text-neutral-500">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="mt-1 font-mono text-sm text-neutral-800" title={value}>
        {truncateHash(value, 8)}
      </p>
    </div>
  );
}

/**
 * Unauthorized (403) Page.
 */

import { Link } from "react-router-dom";
import { ShieldX } from "lucide-react";
import { Button } from "@/components/ui/button";

export function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-danger/10">
        <ShieldX className="h-8 w-8 text-danger" />
      </div>
      <h1 className="text-2xl font-bold text-neutral-800">Access Denied</h1>
      <p className="mt-2 max-w-md text-neutral-500">
        You do not have permission to view this page.
      </p>
      <Link to="/dashboard" className="mt-6">
        <Button>Back to Dashboard</Button>
      </Link>
    </div>
  );
}

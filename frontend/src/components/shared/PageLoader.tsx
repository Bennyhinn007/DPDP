/**
 * Page Loader.
 *
 * Full-page loading state with skeleton-like spinner.
 */

import { Loader2 } from "lucide-react";

export function PageLoader({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
      <p className="mt-3 text-sm text-neutral-500">{message}</p>
    </div>
  );
}

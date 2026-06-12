/**
 * Placeholder Page.
 *
 * Temporary page for routes whose feature UI is built in Phase 2.
 */

import { Construction } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary-50">
            <Construction className="h-7 w-7 text-primary-600" />
          </div>
          <h2 className="text-xl font-semibold text-neutral-800">{title}</h2>
          <p className="mt-2 max-w-md text-sm text-neutral-500">
            This feature page will be implemented in Phase 2. The foundation
            (auth, layout, routing, API layer) is ready.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

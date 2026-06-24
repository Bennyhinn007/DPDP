/**
 * Export Dropdown.
 *
 * Provides PDF and JSON export options for patient data.
 */

import { useState } from "react";
import { Download, FileText, Code, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import api from "@/services/api";

export function ExportDropdown() {
  const [open, setOpen] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const downloadPDF = async () => {
    setDownloading(true);
    try {
      const response = await api.get("/patients/me/export/pdf", { responseType: "blob" });
      const url = URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `health-report-${Date.now()}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("PDF export failed. Ensure reportlab is installed on the backend.");
    } finally {
      setDownloading(false);
      setOpen(false);
    }
  };

  const downloadJSON = async () => {
    setDownloading(true);
    try {
      const { data } = await api.get("/patients/me/export/json");
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `health-data-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("JSON export failed.");
    } finally {
      setDownloading(false);
      setOpen(false);
    }
  };

  return (
    <div className="relative">
      <Button variant="outline" onClick={() => setOpen((o) => !o)} disabled={downloading}>
        <Download className="h-4 w-4" />
        {downloading ? "Exporting..." : "Export Data"}
        <ChevronDown className="h-3.5 w-3.5" />
      </Button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-20 mt-2 w-56 rounded-lg border border-neutral-200 bg-white shadow-lg">
            <div className="p-1">
              <button
                onClick={downloadPDF}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm text-neutral-700 hover:bg-neutral-50"
              >
                <FileText className="h-4 w-4 text-danger" />
                <div className="text-left">
                  <div className="font-medium">Download PDF Report</div>
                  <div className="text-xs text-neutral-400">Patient-friendly format</div>
                </div>
              </button>
              <button
                onClick={downloadJSON}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm text-neutral-700 hover:bg-neutral-50"
              >
                <Code className="h-4 w-4 text-primary-600" />
                <div className="text-left">
                  <div className="font-medium">Download JSON Data</div>
                  <div className="text-xs text-neutral-400">Machine-readable export</div>
                </div>
              </button>
            </div>
            <div className="border-t border-neutral-100 px-3 py-2">
              <p className="text-[10px] text-neutral-400">DPDP Act Section 11 — Right to Data Portability</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Application Root.
 *
 * Sets up providers, routing, and route protection.
 */

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryProvider } from "@/contexts/QueryProvider";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { AppShell } from "@/layouts/AppShell";
import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";
import { PatientDashboard } from "@/pages/patient/PatientDashboard";
import { PersonalDataCenter } from "@/pages/patient/PersonalDataCenter";
import { ConsentCenter } from "@/pages/patient/ConsentCenter";
import { AuditTimeline } from "@/pages/patient/AuditTimeline";
import { IntegrityVerification } from "@/pages/patient/IntegrityVerification";
import { DPODashboard } from "@/pages/dpo/DPODashboard";
import { ComplianceDashboard } from "@/pages/dpo/ComplianceDashboard";
import { PlaceholderPage } from "@/pages/PlaceholderPage";
import { UnauthorizedPage } from "@/pages/UnauthorizedPage";

function App() {
  return (
    <QueryProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />

            {/* Protected (patient) */}
            <Route
              element={
                <ProtectedRoute allowedRoles={["patient"]}>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<PatientDashboard />} />
              <Route path="/my-data" element={<PersonalDataCenter />} />
              <Route path="/consents" element={<ConsentCenter />} />
              <Route path="/timeline" element={<AuditTimeline />} />
              <Route path="/verify" element={<IntegrityVerification />} />
            </Route>

            {/* Protected (admin/dpo) */}
            <Route
              element={
                <ProtectedRoute allowedRoles={["admin", "dpo"]}>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route path="/dpo" element={<DPODashboard />} />
              <Route path="/dpo/compliance" element={<ComplianceDashboard />} />
              <Route path="/compliance" element={<ComplianceDashboard />} />
              <Route path="/admin/users" element={<PlaceholderPage title="User Management" />} />
            </Route>

            {/* Defaults */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryProvider>
  );
}

export default App;

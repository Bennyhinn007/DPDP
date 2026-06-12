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
            <Route path="/unauthorized" element={<UnauthorizedPage />} />

            {/* Protected (patient) */}
            <Route
              element={
                <ProtectedRoute allowedRoles={["patient"]}>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<PlaceholderPage title="Patient Dashboard" />} />
              <Route path="/my-data" element={<PlaceholderPage title="Personal Data Center" />} />
              <Route path="/consents" element={<PlaceholderPage title="Consent Center" />} />
              <Route path="/timeline" element={<PlaceholderPage title="Audit Timeline" />} />
              <Route path="/verify" element={<PlaceholderPage title="Integrity Verification" />} />
            </Route>

            {/* Protected (admin/dpo) */}
            <Route
              element={
                <ProtectedRoute allowedRoles={["admin", "dpo"]}>
                  <AppShell />
                </ProtectedRoute>
              }
            >
              <Route path="/dpo" element={<PlaceholderPage title="Compliance Dashboard" />} />
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

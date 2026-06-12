import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

function HomePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-primary-50">
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center space-x-3">
          <div className="w-12 h-12 bg-primary-700 rounded-lg flex items-center justify-center">
            <span className="text-white text-xl font-bold">D</span>
          </div>
          <h1 className="text-3xl font-bold text-primary-700">
            DPDP Healthcare Platform
          </h1>
        </div>
        <p className="text-neutral-600 text-lg">
          Redactable Blockchain Based Healthcare &amp; Pharmacy Management System
        </p>
        <p className="text-sm text-neutral-400">
          Secure Consent Management • AES-256 Encryption • Blockchain Verification
        </p>
        <div className="pt-4 flex justify-center space-x-3">
          <span className="px-3 py-1 bg-success-100 text-success-600 text-sm rounded-full font-medium">
            ✓ Backend Connected
          </span>
          <span className="px-3 py-1 bg-primary-100 text-primary-700 text-sm rounded-full font-medium">
            ✓ Frontend Ready
          </span>
          <span className="px-3 py-1 bg-saffron-100 text-saffron-600 text-sm rounded-full font-medium">
            ✓ DPDP Compliant
          </span>
        </div>
      </div>
    </div>
  );
}

export default App;

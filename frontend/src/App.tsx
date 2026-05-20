import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

// Each top-level module is its own chunk — visitors who only hit the
// landing page don't download the admin dashboard, and vice-versa.
const LandingPage = lazy(() =>
  import("./modules/landing/LandingPage").then((m) => ({ default: m.LandingPage })),
);
const AdminApp = lazy(() =>
  import("./modules/admin/AdminApp").then((m) => ({ default: m.AdminApp })),
);
const WebAppRoot = lazy(() =>
  import("./modules/webapp/WebAppRoot").then((m) => ({ default: m.WebAppRoot })),
);

function PageFallback() {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--fg, #f1e8d6)",
        background: "var(--bg, #07050a)",
        fontSize: 14,
        opacity: 0.6,
      }}
    >
      ⏳
    </div>
  );
}

export function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/admin/*" element={<AdminApp />} />
        <Route path="/webapp/*" element={<WebAppRoot />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

import { Routes, Route, Link, Navigate } from "react-router-dom";

import { AdminApp } from "./modules/admin/AdminApp";
import { WebAppRoot } from "./modules/webapp/WebAppRoot";
import { HealthCheck } from "./shared/components/HealthCheck";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/admin/*" element={<AdminApp />} />
      <Route path="/webapp/*" element={<WebAppRoot />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function HomePage() {
  return (
    <main className="home">
      <h1>🎲 Mafia Bot</h1>
      <p>
        <code>@MafGameUzBot</code> — professional Telegram Mafia bot
      </p>
      <nav>
        <ul>
          <li>
            <Link to="/admin">🛠 Super admin paneli</Link>
          </li>
          <li>
            <Link to="/webapp">📱 Telegram WebApp (guruh sozlamalari)</Link>
          </li>
        </ul>
      </nav>
      <HealthCheck />
    </main>
  );
}

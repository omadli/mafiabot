import { Link } from "react-router-dom";

export function AdminApp() {
  return (
    <main className="home">
      <h1>🛠 Super admin paneli</h1>
      <p>
        Bosqich 3 da to'liq qo'llanadi: Dashboard, Users, Groups, Stats, Audit, WebSocket real-time
        updates.
      </p>
      <Link to="/">← Bosh sahifa</Link>
    </main>
  );
}

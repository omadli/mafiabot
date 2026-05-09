import { useEffect } from "react";
import { Link } from "react-router-dom";
import WebApp from "@twa-dev/sdk";

export function WebAppRoot() {
  useEffect(() => {
    if (typeof WebApp !== "undefined" && WebApp.ready) {
      WebApp.ready();
      WebApp.expand();
    }
  }, []);

  return (
    <main className="home">
      <h1>📱 Telegram WebApp</h1>
      <p>
        Guruh adminlari uchun sozlamalar UI'si — Bosqich 3 da to'liq qo'llanadi: rollar
        nisbati, vaqtlar, til, AFK qoidalari.
      </p>
      <Link to="/">← Bosh sahifa</Link>
    </main>
  );
}

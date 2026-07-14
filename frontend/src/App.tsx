import { useEffect, useState } from "react";

import { login } from "./api/client";
import { clearSession, loadSession, saveSession } from "./auth/session";
import { LoginPage } from "./components/LoginPage";
import { DashboardPage } from "./components/DashboardPage";
import { clearClientKey } from "./utils/credentialTransport";
import type { AuthSession } from "./types";

function App() {
  const [session, setSession] = useState<AuthSession | null>(() => loadSession());

  useEffect(() => {
    const handleExpired = () => { clearClientKey(); setSession(null); };
    window.addEventListener("auth-expired", handleExpired);
    return () => window.removeEventListener("auth-expired", handleExpired);
  }, []);

  useEffect(() => {
    if (!session) return;
    let timeout = 0;
    const checkExpiry = () => {
      const remaining = session.expiresAt - Date.now();
      if (remaining <= 0) {
        clearClientKey();
        clearSession();
        setSession(null);
        return;
      }
      timeout = window.setTimeout(checkExpiry, Math.min(remaining, 24 * 60 * 60 * 1000));
    };
    checkExpiry();
    return () => window.clearTimeout(timeout);
  }, [session]);

  if (!session) {
    return <LoginPage onLogin={async (username, password) => { const nextSession = await login(username, password); saveSession(nextSession); setSession(nextSession); return nextSession; }} />;
  }

  return <DashboardPage session={session} onLogout={() => { clearClientKey(); clearSession(); setSession(null); }} />;
}

export default App;

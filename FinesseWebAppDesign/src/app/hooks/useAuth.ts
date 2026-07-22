import { useCallback, useEffect, useState } from "react";
import { getCsrfToken } from "../lib/csrf";

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  linked_accounts?: { platform: string; platform_username: string; is_primary: boolean; rating: number | null }[];
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/auth/status/", { credentials: "same-origin" });
      if (!res.ok) throw new Error("Auth check failed");
      const data = await res.json();
      setUser(data.authenticated ? data.user : null);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(() => {
    // Redirect to allauth login page; on success allauth redirects back to /
    window.location.href = "/accounts/login/";
  }, []);

  const register = useCallback(() => {
    window.location.href = "/accounts/signup/";
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch("/accounts/logout/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": getCsrfToken() },
      });
    } catch {
      // ignore
    }
    setUser(null);
    window.location.href = "/";
  }, []);

  return { user, loading, isAuthenticated: !!user, login, register, logout, refresh };
}

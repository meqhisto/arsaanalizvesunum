"use client";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getProfile, login as apiLogin, logout as apiLogout } from "@/lib/auth";

type AuthContextType = {
  user: any | null;
  isAuthenticated: boolean;
  login: (email: string, password: string, remember?: boolean) => Promise<void>;
  logout: () => void;
  reload: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any | null>(null);
  const isAuthenticated = !!user;

  const reload = useCallback(async () => {
    try {
      const profile = await getProfile();
      setUser(profile);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const login = useCallback(async (email: string, password: string, remember = false) => {
    await apiLogin(email, password, remember);
    await reload();
  }, [reload]);

  const logout = useCallback(() => {
    apiLogout();
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, isAuthenticated, login, logout, reload }), [user, isAuthenticated, login, logout, reload]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}


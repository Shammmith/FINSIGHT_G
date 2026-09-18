"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "@/services/api";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("token");
    if (stored) {
      setToken(stored);
      api.defaults.headers.common["Authorization"] = `Bearer ${stored}`;
    }
  }, []);

  const login = (newToken: string) => {
    localStorage.setItem("token", newToken);
    api.defaults.headers.common["Authorization"] = `Bearer ${newToken}`;
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem("token");
    delete api.defaults.headers.common["Authorization"];
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
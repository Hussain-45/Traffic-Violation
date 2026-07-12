"use client";

import React, { createContext, useContext, useState, useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import { BACKEND_URL } from "@/lib/apiClient";

interface UserMe {
  id: number;
  username: str;
  email: string;
  full_name: string;
  role: string;
  permissions: string[];
}

interface AuthContextProps {
  user: UserMe | null;
  token: string | null;
  loading: boolean;
  login: (username: str, password: str, rememberMe: boolean) => Promise<boolean>;
  logout: () => Promise<void>;
  changePassword: (oldPass: str, newPass: str) => Promise<boolean>;
  hasPermission: (permission: str) => boolean;
}

const AuthContext = createContext<AuthContextProps | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const mockUser: UserMe = {
    id: 1,
    username: "admin",
    email: "admin@smarttraffic.gov.in",
    full_name: "Super Admin",
    role: "admin",
    permissions: [
      "dashboard", "analytics", "reports", "evidence", "email",
      "settings", "users", "cameras", "system_logs", "system_health",
      "violation_review", "configuration", "exports"
    ]
  };

  const [user, setUser] = useState<UserMe | null>(mockUser);
  const [token, setToken] = useState<string | null>("mock_admin_token");
  const [loading, setLoading] = useState(false);

  const router = useRouter();

  useEffect(() => {
    setToken("mock_admin_token");
    setUser(mockUser);
    setLoading(false);
  }, []);

  const login = async (usernameInput: string, passwordInput: string, rememberMe: boolean): Promise<boolean> => {
    setToken("mock_admin_token");
    setUser(mockUser);
    return true;
  };

  const logout = async () => {
    router.push("/");
  };

  const changePassword = async (oldPass: string, newPass: string): Promise<boolean> => {
    return true;
  };

  const hasPermission = (permission_name: string): boolean => {
    return true;
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, changePassword, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

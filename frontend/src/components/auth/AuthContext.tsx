"use client";

import React, { createContext, useContext, useState, useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";

const BACKEND_URL = "http://localhost:8000";

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
  const [user, setUser] = useState<UserMe | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showTimeoutDialog, setShowTimeoutDialog] = useState(false);
  const [secondsRemaining, setSecondsRemaining] = useState(60);

  const router = useRouter();
  const pathname = usePathname();
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);
  const warningTimerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Sync token from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("auth_access_token");
    if (savedToken) {
      setToken(savedToken);
      fetchUserProfile(savedToken);
    } else {
      setLoading(false);
    }
  }, []);

  // Setup timers when token is active
  useEffect(() => {
    if (token) {
      scheduleTokenRefresh(token);
    } else {
      clearAllTimers();
    }
    return () => clearAllTimers();
  }, [token]);

  const clearAllTimers = () => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    if (warningTimerRef.current) clearTimeout(warningTimerRef.current);
    if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
  };

  const fetchUserProfile = async (accessToken: string) => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
        headers: {
          "Authorization": `Bearer ${accessToken}`,
          "Content-Type": "application/json"
        }
      });
      if (res.ok) {
        const profile = await res.json();
        setUser(profile);
      } else {
        // Token invalid, clear it
        handleLogoutClear();
      }
    } catch {
      handleLogoutClear();
    } finally {
      setLoading(false);
    }
  };

  const scheduleTokenRefresh = (accessToken: string) => {
    clearAllTimers();
    try {
      // Decode JWT roughly to extract exp
      const payloadBase64 = accessToken.split(".")[1];
      const payload = JSON.parse(atob(payloadBase64));
      const exp = payload.exp * 1000; // in ms
      const now = Date.now();
      const timeRemaining = exp - now;

      if (timeRemaining <= 0) {
        handleLogoutClear();
        return;
      }

      // 1. Schedule automatic token refresh 1 minute before expiration
      const refreshDelay = Math.max(0, timeRemaining - 60000);
      refreshTimerRef.current = setTimeout(triggerTokenRefresh, refreshDelay);

      // 2. Schedule session timeout warning dialog 60 seconds before expiration
      const warningDelay = Math.max(0, timeRemaining - 60000);
      warningTimerRef.current = setTimeout(() => {
        setShowTimeoutDialog(true);
        setSecondsRemaining(60);
        // Start countdown
        countdownTimerRef.current = setInterval(() => {
          setSecondsRemaining((prev) => {
            if (prev <= 1) {
              handleLogoutClear();
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
      }, warningDelay);

    } catch (e) {
      console.error("Failed to parse JWT payload expirations", e);
    }
  };

  const triggerTokenRefresh = async () => {
    const savedRefresh = localStorage.getItem("auth_refresh_token");
    if (!savedRefresh) {
      handleLogoutClear();
      return;
    }
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: savedRefresh })
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("auth_access_token", data.access_token);
        localStorage.setItem("auth_refresh_token", data.refresh_token);
        setToken(data.access_token);
        setShowTimeoutDialog(false);
        clearAllTimers();
      } else {
        handleLogoutClear();
      }
    } catch {
      handleLogoutClear();
    }
  };

  const login = async (usernameInput: string, passwordInput: string, rememberMe: boolean): Promise<boolean> => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: usernameInput, password: passwordInput, remember_me: rememberMe })
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Credentials authentication failed.");
      }
      const data = await res.json();
      localStorage.setItem("auth_access_token", data.access_token);
      localStorage.setItem("auth_refresh_token", data.refresh_token);
      setToken(data.access_token);
      await fetchUserProfile(data.access_token);
      return true;
    } catch (err: any) {
      alert(err.message || "Failed to authenticate.");
      return false;
    }
  };

  const logout = async () => {
    if (token) {
      try {
        await fetch(`${BACKEND_URL}/api/v1/auth/logout`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });
      } catch {}
    }
    handleLogoutClear();
  };

  const handleLogoutClear = () => {
    localStorage.removeItem("auth_access_token");
    localStorage.removeItem("auth_refresh_token");
    setToken(null);
    setUser(null);
    setShowTimeoutDialog(false);
    clearAllTimers();
    router.push("/login");
  };

  const changePassword = async (oldPass: string, newPass: string): Promise<boolean> => {
    if (!token) return false;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/auth/change-password`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ old_password: oldPass, new_password: newPass })
      });
      return res.ok;
    } catch {
      return false;
    }
  };

  const hasPermission = (permission_name: string): boolean => {
    if (!user) return false;
    return user.permissions.includes(permission_name);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, changePassword, hasPermission }}>
      {children}

      {/* Session Timeout Dialog Modal */}
      {showTimeoutDialog && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-navy-light rounded-lg border border-navy-accent max-w-sm w-full p-6 shadow-2xl">
            <h3 className="font-bold text-slate-100 text-lg flex items-center gap-2">
              <span>⏳</span> Session Expiring Soon
            </h3>
            <p className="text-sm text-slate-400 mt-2">
              Your security session will automatically timeout in <span className="font-mono text-brand-cyan font-bold">{secondsRemaining}</span> seconds due to inactivity.
            </p>
            <div className="mt-6 flex justify-end gap-3.5">
              <button
                onClick={logout}
                className="px-4 py-2 text-xs font-semibold bg-navy-accent hover:bg-navy-accent/70 rounded-lg text-slate-300 transition-colors"
              >
                Log Out
              </button>
              <button
                onClick={triggerTokenRefresh}
                className="px-4 py-2 text-xs font-semibold bg-brand-cyan hover:bg-brand-cyan/80 text-navy-darker rounded-lg transition-colors"
              >
                Keep Me Signed In
              </button>
            </div>
          </div>
        </div>
      )}
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

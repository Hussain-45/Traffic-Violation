"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

const BACKEND_BASE_URL = "http://localhost:8000";

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/v1/health`, {
      method: "GET",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === "ok";
  } catch (error) {
    return false;
  }
}

interface AppContextProps {
  backendOnline: boolean;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  triggerHealthCheck: () => Promise<void>;
}

const AppContext = createContext<AppContextProps | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);

  const triggerHealthCheck = async () => {
    const online = await checkBackendHealth();
    setBackendOnline(online);
  };

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => !prev);
  };

  // Poll backend health status every 5 seconds
  useEffect(() => {
    triggerHealthCheck();
    const interval = setInterval(triggerHealthCheck, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <AppContext.Provider
      value={{
        backendOnline,
        sidebarCollapsed,
        setSidebarCollapsed,
        toggleSidebar,
        triggerHealthCheck,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}

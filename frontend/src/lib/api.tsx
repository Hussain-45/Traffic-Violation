"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { BACKEND_URL, fetchWithTimeout } from "./apiClient";

export async function checkBackendHealth(): Promise<boolean> {
  const maxRetries = 3;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetchWithTimeout(`${BACKEND_URL}/api/v1/health`, {
        method: "GET",
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
        },
        timeout: 5000, // 5s timeout for health checks
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "ok") return true;
      }
    } catch (error) {
      if (attempt === maxRetries) return false;
    }
    // Small delay between retries
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  return false;
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
  const [backendOnline, setBackendOnline] = useState<boolean>(true); // start as true to prevent flash offline skeletons
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

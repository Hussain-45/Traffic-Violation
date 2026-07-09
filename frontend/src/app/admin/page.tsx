"use client";

import React, { useState, useEffect, useRef } from "react";
import { useApp } from "../../lib/api";
import { SystemStatusCard } from "../../components/admin/SystemStatusCard";
import { CameraControlTable } from "../../components/admin/CameraControlTable";
import { UserManagementTable } from "../../components/admin/UserManagementTable";
import { ConfigSettingsForm } from "../../components/admin/ConfigSettingsForm";
import { LogViewerConsole } from "../../components/admin/LogViewerConsole";
import { Button } from "../../components/ui/Button";
import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui/Card";

const BACKEND_URL = "http://localhost:8000";

interface NotificationEvent {
  level: string;
  source: string;
  message: string;
  timestamp: number;
}

export default function AdminDashboardPage() {
  const { backendOnline } = useApp();
  const [token, setToken] = useState<string | null>(null);
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(false);
  const [userRole, setUserRole] = useState<string>("viewer");

  // Tab State
  const [activeTab, setActiveTab] = useState("overview");

  // Live Refresh Configs
  const [refreshInterval, setRefreshInterval] = useState<number>(5000); // in ms (5s default)
  const [countdown, setCountdown] = useState<number>(5);

  // API Data States
  const [summary, setSummary] = useState<any>(null);
  const [statusData, setStatusData] = useState<any>(null);
  const [cameras, setCameras] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [settings, setSettings] = useState<any>(null);
  const [logs, setLogs] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [notifications, setNotifications] = useState<NotificationEvent[]>([]);

  const [loadingData, setLoadingData] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load token and role from localStorage
  useEffect(() => {
    const savedToken = localStorage.getItem("admin_access_token");
    const savedRole = localStorage.getItem("admin_role");
    if (savedToken) {
      setToken(savedToken);
      setUserRole(savedRole || "viewer");
    }
  }, []);

  // Fetch admin dashboard details
  const fetchAllAdminData = async () => {
    if (!token || !backendOnline) return;
    setLoadingData(true);
    setErrorMsg(null);
    try {
      const headers = {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      };

      // Fetch dashboard summary
      const summaryRes = await fetch(`${BACKEND_URL}/api/v1/admin/dashboard`, { headers });
      if (summaryRes.status === 401 || summaryRes.status === 403) {
        handleLogout();
        return;
      }
      const summaryData = await summaryRes.json();
      setSummary(summaryData);

      // Fetch system status
      const statusRes = await fetch(`${BACKEND_URL}/api/v1/admin/system`, { headers });
      const systemData = await statusRes.json();
      setStatusData(systemData);

      // Fetch cameras
      const camRes = await fetch(`${BACKEND_URL}/api/v1/admin/cameras`, { headers });
      const camData = await camRes.json();
      setCameras(camData);

      // Fetch users
      const userRes = await fetch(`${BACKEND_URL}/api/v1/admin/users`, { headers });
      const userData = await userRes.json();
      setUsers(userData);

      // Fetch settings
      const settingsRes = await fetch(`${BACKEND_URL}/api/v1/admin/settings`, { headers });
      const configData = await settingsRes.json();
      setSettings(configData);

      // Fetch health
      const healthRes = await fetch(`${BACKEND_URL}/api/v1/admin/health`, { headers });
      const healthData = await healthRes.json();
      setHealth(healthData);

      // Fetch logs
      const logsRes = await fetch(`${BACKEND_URL}/api/v1/admin/logs?lines=100`, { headers });
      const logsData = await logsRes.json();
      setLogs(logsData);

      // Simulate notifications generation from status
      const newAlerts: NotificationEvent[] = [];
      if (healthData && !healthData.database) {
        newAlerts.push({ level: "error", source: "database", message: "Database link lost.", timestamp: Date.now() });
      }
      if (systemData && systemData.disk_percent > 85.0) {
        newAlerts.push({ level: "warning", source: "storage", message: "Disk usage is critically high.", timestamp: Date.now() });
      }
      if (systemData && systemData.cpu_percent > 90.0) {
        newAlerts.push({ level: "warning", source: "cpu", message: "CPU utilization exceeding 90%.", timestamp: Date.now() });
      }
      setNotifications(newAlerts);

    } catch (err: any) {
      setErrorMsg("Failed to retrieve admin control configurations.");
    } finally {
      setLoadingData(false);
    }
  };

  // Live Refresh interval handling
  useEffect(() => {
    if (!token || refreshInterval === 0) return;

    setCountdown(refreshInterval / 1000);
    const countdownTimer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          fetchAllAdminData();
          return refreshInterval / 1000;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(countdownTimer);
  }, [token, refreshInterval, backendOnline]);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingAuth(true);
    setAuthError(null);

    try {
      // API expects application/x-www-form-urlencoded
      const formData = new URLSearchParams();
      formData.append("username", usernameInput);
      formData.append("password", passwordInput);

      const res = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData.toString(),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Authentication failed.");
      }

      const data = await res.json();
      localStorage.setItem("admin_access_token", data.access_token);
      
      // Decode JWT roughly to extract role (for demo/permissions client side)
      let role = "admin"; // default fallback for admin login
      try {
        const payloadBase64 = data.access_token.split(".")[1];
        const payload = JSON.parse(atob(payloadBase64));
        role = payload.role || "admin";
      } catch (e) {}

      localStorage.setItem("admin_role", role);
      setToken(data.access_token);
      setUserRole(role);
    } catch (err: any) {
      setAuthError(err.message || "Invalid administrator credentials.");
    } finally {
      setLoadingAuth(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("admin_access_token");
    localStorage.removeItem("admin_role");
    setToken(null);
    setUserRole("viewer");
    setSummary(null);
    setStatusData(null);
    setCameras([]);
    setUsers([]);
    setSettings(null);
    setLogs(null);
  };

  // Camera Actions
  const handleToggleCamera = async (camera_id: string, enabled: boolean) => {
    if (!token) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/admin/cameras/${camera_id}/toggle`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ enabled }),
      });
      if (res.ok) {
        await fetchAllAdminData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRestartCamera = async (camera_id: string) => {
    if (!token) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/admin/cameras/${camera_id}/restart`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        alert("Camera restart signal triggered successfully.");
        await fetchAllAdminData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // User Actions
  const handleUpdateUser = async (user_id: number, role: string, status: string) => {
    if (!token) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/admin/users/${user_id}`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ role, status }),
      });
      if (res.ok) {
        await fetchAllAdminData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Settings Action
  const handleSaveSettings = async (updatedSettings: any) => {
    if (!token) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/admin/settings`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updatedSettings),
      });
      if (res.ok) {
        alert("Configuration parameters updated dynamically.");
        await fetchAllAdminData();
      } else {
        alert("Failed to save configurations.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRefreshLogs = async () => {
    if (!token) return;
    try {
      const logsRes = await fetch(`${BACKEND_URL}/api/v1/admin/logs?lines=100`, {
        headers: { "Authorization": `Bearer ${token}` },
      });
      const logsData = await logsRes.json();
      setLogs(logsData);
    } catch (err) {
      console.error(err);
    }
  };

  // Render Login overlay if token is not active
  if (!token) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-4">
        <div className="bg-navy-light/40 border border-navy-accent/50 p-8 rounded-2xl w-full max-w-md shadow-2xl backdrop-blur-md">
          <div className="text-center mb-6">
            <div className="w-12 h-12 bg-gradient-to-tr from-brand-blue to-brand-cyan rounded-xl flex items-center justify-center font-bold text-lg text-white mx-auto shadow-lg shadow-brand-cyan/20">
              🛡️
            </div>
            <h2 className="text-xl font-bold text-slate-100 mt-4">Administrator Access</h2>
            <p className="text-xs text-slate-400 mt-1">Please log in to manage configuration and nodes.</p>
          </div>

          <form onSubmit={handleLoginSubmit} className="space-y-4">
            {authError && (
              <div className="bg-status-red/10 border border-status-red/30 text-status-red text-xs p-3.5 rounded-lg font-medium">
                ⚠️ {authError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Username</label>
              <input
                type="text"
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Password</label>
              <input
                type="password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
                required
              />
            </div>

            <Button variant="primary" type="submit" className="w-full" disabled={loadingAuth}>
              {loadingAuth ? "Authorizing access..." : "Authenticate Administrator"}
            </Button>
          </form>
        </div>
      </div>
    );
  }

  // RBAC protection - Hide page if not admin/officer
  if (userRole !== "admin" && userRole !== "officer") {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6">
        <div className="text-5xl mb-4">🚫</div>
        <h2 className="text-xl font-bold text-slate-100">Privileged View Restricted</h2>
        <p className="text-sm text-slate-400 mt-2 max-w-sm">
          Your account role ({userRole}) does not have administrative clearance to access settings or system controls.
        </p>
        <Button variant="secondary" className="mt-6" onClick={handleLogout}>
          Authenticate with another account
        </Button>
      </div>
    );
  }

  if (loadingData && !summary) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-brand-cyan border-t-transparent rounded-full animate-spin" />
        <span className="text-slate-400 text-sm">Retrieving system states...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header section with logout and refresh interval controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-navy-accent/30 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <span>🛡️</span> Admin Management Console
          </h1>
          <p className="text-xs text-slate-400 mt-1">Configure active models, manage camera nodes, update users, and inspect logs.</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {/* Configurable Live Refresh */}
          <div className="flex items-center gap-2 bg-navy-light px-3 py-1.5 rounded-lg border border-navy-accent/40 text-xs text-slate-300">
            <span>Interval:</span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="bg-navy-dark border border-navy-accent/50 text-slate-300 rounded p-1 hover:border-brand-cyan/45 focus:outline-none cursor-pointer font-semibold"
            >
              <option value={5000}>5s Refresh</option>
              <option value={10000}>10s Refresh</option>
              <option value={30000}>30s Refresh</option>
              <option value={0}>Manual Only</option>
            </select>
            {refreshInterval > 0 && (
              <span className="font-mono text-brand-cyan ml-1 w-4 block text-right">{countdown}s</span>
            )}
          </div>

          <Button variant="outline" size="sm" onClick={fetchAllAdminData}>
            🔄 Force Refresh
          </Button>

          <Button variant="secondary" size="sm" onClick={handleLogout}>
            🔌 Log Out
          </Button>
        </div>
      </div>

      {/* Notification Center */}
      {notifications.length > 0 && (
        <div className="bg-navy-light border-l-4 border-status-red rounded-r-xl p-4 space-y-2.5 shadow-lg shadow-status-red/5">
          <div className="flex items-center gap-2 text-status-red font-bold text-sm uppercase tracking-wide">
            <span>⚠️</span> Active System Notifications / Alerts ({notifications.length})
          </div>
          <div className="space-y-1.5">
            {notifications.map((alert, idx) => (
              <div key={idx} className="text-xs text-slate-300 flex items-center justify-between">
                <span>• {alert.message} (Source: <span className="font-mono text-brand-cyan">{alert.source}</span>)</span>
                <span className="text-[10px] text-slate-500 font-mono">{new Date(alert.timestamp).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Grid summary cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="hover:border-brand-cyan/25 transition-colors">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Total Violations</span>
              <span className="text-2xl">🚨</span>
            </CardHeader>
            <CardContent>
              <h3 className="text-3xl font-bold text-slate-100 font-mono">{summary.total_violations}</h3>
              <p className="text-[10px] text-slate-500 mt-1">Sum of all vehicle violations captured.</p>
            </CardContent>
          </Card>

          <Card className="hover:border-brand-cyan/25 transition-colors">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Active Cameras</span>
              <span className="text-2xl">🎥</span>
            </CardHeader>
            <CardContent>
              <h3 className="text-3xl font-bold text-slate-100 font-mono">
                {summary.online_cameras} <span className="text-slate-500 text-lg">/ {summary.total_cameras}</span>
              </h3>
              <p className="text-[10px] text-slate-500 mt-1">Online camera node channels ratio.</p>
            </CardContent>
          </Card>

          <Card className="hover:border-brand-cyan/25 transition-colors">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Active Users</span>
              <span className="text-2xl">👥</span>
            </CardHeader>
            <CardContent>
              <h3 className="text-3xl font-bold text-slate-100 font-mono">
                {summary.active_users} <span className="text-slate-500 text-lg">/ {summary.total_users}</span>
              </h3>
              <p className="text-[10px] text-slate-500 mt-1">Chronological user states recorded.</p>
            </CardContent>
          </Card>

          <Card className="hover:border-brand-cyan/25 transition-colors">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">OCR Success Rate</span>
              <span className="text-2xl">🔍</span>
            </CardHeader>
            <CardContent>
              <h3 className="text-3xl font-bold text-slate-100 font-mono">
                {summary.ocr_statistics?.requests_count > 0
                  ? ((summary.ocr_statistics.verified_count / summary.ocr_statistics.requests_count) * 100).toFixed(1)
                  : "0.0"}%
              </h3>
              <p className="text-[10px] text-slate-500 mt-1">Verified OCR confidence conversion ratio.</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs list */}
      <div className="flex border-b border-navy-accent/40 gap-6">
        {[
          { id: "overview", label: "System Resources", icon: "📊" },
          { id: "cameras", label: "Camera Nodes", icon: "🎥" },
          { id: "users", label: "User Management", icon: "👥" },
          { id: "settings", label: "Pipeline Settings", icon: "⚙️" },
          { id: "logs", label: "Audit Trails & Logs", icon: "📄" },
        ].map((tab) => {
          // RBAC check: Only admins can manage users and settings
          if (userRole !== "admin" && (tab.id === "users" || tab.id === "settings")) {
            return null;
          }
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3.5 text-sm font-medium transition-all duration-200 border-b-2 flex items-center gap-2 cursor-pointer ${
                activeTab === tab.id
                  ? "border-brand-cyan text-brand-cyan"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "overview" && statusData && (
          <SystemStatusCard statusData={statusData} healthData={health} />
        )}

        {activeTab === "cameras" && cameras && (
          <CameraControlTable
            cameras={cameras}
            onToggle={handleToggleCamera}
            onRestart={handleRestartCamera}
          />
        )}

        {activeTab === "users" && userRole === "admin" && users && (
          <UserManagementTable users={users} onUpdate={handleUpdateUser} />
        )}

        {activeTab === "settings" && userRole === "admin" && settings && (
          <ConfigSettingsForm settings={settings} onSave={handleSaveSettings} />
        )}

        {activeTab === "logs" && logs && (
          <LogViewerConsole logsData={logs} onRefresh={handleRefreshLogs} />
        )}
      </div>
    </div>
  );
}

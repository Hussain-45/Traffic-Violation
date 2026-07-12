"use client";

import { useAuth } from "@/components/auth/AuthContext";
import { useApp } from "@/lib/api";
import { BACKEND_URL } from "@/lib/apiClient";
import { useEffect, useState } from "react";
import { CameraControlTable } from "../../components/admin/CameraControlTable";
import { ConfigSettingsForm } from "../../components/admin/ConfigSettingsForm";
import { LogViewerConsole } from "../../components/admin/LogViewerConsole";
import { SystemStatusCard } from "../../components/admin/SystemStatusCard";
import { UserManagementTable } from "../../components/admin/UserManagementTable";
import { Button } from "../../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/Card";

interface NotificationEvent {
  level: string;
  source: string;
  message: string;
  timestamp: number;
}

export default function AdminDashboardPage() {
  const { token, user, logout } = useAuth();
  const { backendOnline } = useApp();

  // Tab State
  const [activeTab, setActiveTab] = useState("overview");

  // Live Refresh Configs
  const [refreshInterval, setRefreshInterval] = useState<number>(5000); // in ms
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
        logout();
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

      // Compile notifications
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

  useEffect(() => {
    if (token) {
      fetchAllAdminData();
    }
  }, [token, backendOnline]);

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
        fetchAllAdminData();
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
        fetchAllAdminData();
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
        fetchAllAdminData();
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
        fetchAllAdminData();
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

  // RBAC protection - Hide page if not admin/officer
  if (user?.role !== "admin" && user?.role !== "officer") {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center p-6">
        <div className="text-5xl mb-4">🚫</div>
        <h2 className="text-xl font-bold text-slate-100">Privileged View Restricted</h2>
        <p className="text-sm text-slate-400 mt-2 max-w-sm">
          Your account role does not have administrative clearance to access settings or system controls.
        </p>
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
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-navy-accent/30 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <span>🛡️</span> Admin Management Console
          </h1>
          <p className="text-xs text-slate-400 mt-1">Configure active models, manage camera nodes, update users, and inspect logs.</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
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
          if (user?.role !== "admin" && (tab.id === "users" || tab.id === "settings")) {
            return null;
          }
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3.5 text-sm font-medium transition-all duration-200 border-b-2 flex items-center gap-2 cursor-pointer ${activeTab === tab.id
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

        {activeTab === "users" && user?.role === "admin" && users && (
          <UserManagementTable users={users} onUpdate={handleUpdateUser} />
        )}

        {activeTab === "settings" && user?.role === "admin" && settings && (
          <ConfigSettingsForm settings={settings} onSave={handleSaveSettings} />
        )}

        {activeTab === "logs" && logs && (
          <LogViewerConsole logsData={logs} onRefresh={handleRefreshLogs} />
        )}
      </div>
    </div>
  );
}

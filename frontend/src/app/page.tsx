"use client";

import React, { useState, useEffect } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/components/auth/AuthContext";
import { useApp } from "@/lib/api";
import { BACKEND_URL } from "@/lib/apiClient";

export default function Home() {
  const { token, user } = useAuth();
  const { backendOnline } = useApp();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchDashboardStats = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/dashboard/stats`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      } else {
        setErrorMsg("Failed to retrieve dashboard telemetry metrics.");
      }
    } catch {
      setErrorMsg("Unable to connect to backend server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchDashboardStats();
    }
  }, [token, backendOnline]);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-brand-cyan border-t-transparent rounded-full animate-spin" />
        <span className="text-slate-400 text-sm">Compiling dashboard stats...</span>
      </div>
    );
  }

  const summary = stats?.summary || {
    total_vehicles: 0,
    total_violations: 0,
    today_violations: 0,
    fines_collected: 0,
    fines_pending: 0,
    total_cameras: 0,
    online_cameras: 0,
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <PageHeader
        title="Dashboard Overview"
        description="Monitor traffic status, active violation detections, and camera analytics feeds in real-time."
      >
        <Button variant="outline" size="sm" onClick={fetchDashboardStats}>
          🔄 Refresh
        </Button>
        <Button variant="primary" size="sm" onClick={() => window.location.href = "/live"}>
          🎥 Live Feed
        </Button>
      </PageHeader>

      {/* Grid of Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
        <StatCard
          title="Today's Violations"
          value={String(summary.today_violations)}
          icon={<span>🚨</span>}
          description="Captured within last 24 hours"
        />

        <StatCard
          title="Active Cameras"
          value={`${summary.online_cameras} / ${summary.total_cameras}`}
          icon={<span>🎥</span>}
          description="Online camera channels ratio"
        />

        <StatCard
          title="Vehicles Detected"
          value={summary.total_vehicles.toLocaleString()}
          icon={<span>🚗</span>}
          description="Sum of all processed tracks"
        />

        <StatCard
          title="Pending Challans"
          value={`₹${summary.fines_pending.toLocaleString()}`}
          icon={<span>💸</span>}
          description="Awaiting officer resolution"
        />

        <StatCard
          title="System Status"
          value={backendOnline ? "Operational" : "Offline"}
          icon={<span>🛡️</span>}
          description={backendOnline ? "All services online" : "Connection lost"}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Active Traffic Feed Tracker</CardTitle>
                <p className="text-xs text-slate-400 mt-1">Real-time inference video overlay</p>
              </div>
              <Badge variant="info">LIVE FEED</Badge>
            </CardHeader>
            <CardContent>
              <div className="aspect-video w-full rounded-lg bg-navy-dark border border-navy-accent/50 flex flex-col items-center justify-center relative overflow-hidden group">
                {backendOnline ? (
                  <img
                    src={`${BACKEND_URL}/api/v1/camera/stream`}
                    alt="Active Video Stream"
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = "none";
                    }}
                  />
                ) : (
                  <>
                    <span className="text-sm font-semibold tracking-wider text-slate-400 uppercase">
                      Camera Feed Offline
                    </span>
                    <span className="text-xs text-slate-500 mt-1">
                      Enable live feeds on the Live Monitoring tab.
                    </span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card className="h-full flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recent Violations Log</CardTitle>
                <p className="text-xs text-slate-400 mt-1">Real-time detection events</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => window.location.href = "/violations"}>
                View All
              </Button>
            </CardHeader>
            <CardContent className="flex-1 space-y-4 overflow-y-auto max-h-[350px]">
              {stats?.recent_violations?.length > 0 ? (
                stats.recent_violations.map((item: any) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-navy-dark/40 border border-navy-accent/20 hover:border-navy-accent/40 transition-colors"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-slate-200 font-bold">{item.plate}</span>
                        <Badge variant="danger">{item.type}</Badge>
                      </div>
                      <span className="text-[10px] text-slate-500 block">
                        ID: #{item.id} • {new Date(item.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-slate-300">
                      ₹{item.fine_amount}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-slate-500 text-xs">
                  No violations captured today.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

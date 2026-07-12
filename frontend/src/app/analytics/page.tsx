"use client";

import React, { useState, useEffect } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { useAuth } from "@/components/auth/AuthContext";
import { useApp } from "@/lib/api";
import { BACKEND_URL } from "@/lib/apiClient";

export default function AnalyticsPage() {
  const { token } = useAuth();
  const { backendOnline } = useApp();

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [filterTime, setFilterTime] = useState("last_month");
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const triggerToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchAnalytics = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/analytics/charts?time_span=${filterTime}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        const result = await res.json();
        setData(result);
      } else {
        triggerToast("Failed to retrieve system telemetry metrics.", "error");
      }
    } catch {
      triggerToast("Error connecting to analytics database.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchAnalytics();
    }
  }, [token, filterTime, backendOnline]);

  const handleExport = (format: "csv" | "xlsx") => {
    window.open(`${BACKEND_URL}/api/v1/analytics/export?format=${format}&token=${token}`, "_blank");
    triggerToast(`Initiated ${format.toUpperCase()} export download.`);
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-brand-cyan border-t-transparent rounded-full animate-spin" />
        <span className="text-slate-400 text-xs">Compiling analytical databases...</span>
      </div>
    );
  }

  // Fallbacks if data empty
  const categories = data?.categories || [];
  const vehicleTypes = data?.vehicle_types || [];
  const hourlyTrends = data?.hourly_trends || [];
  const monthlyTrends = data?.monthly_trends || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-xl text-white text-xs font-semibold flex items-center gap-2 ${
          toast.type === "success" ? "bg-emerald-600" : "bg-rose-600"
        }`}>
          <span>{toast.type === "success" ? "✓" : "⚠️"}</span>
          <span>{toast.message}</span>
        </div>
      )}

      <PageHeader
        title="Metrics & Charts"
        description="Visualize hourly traffic flow counts, violation distribution matrices, and intersection performance stats."
      >
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={filterTime}
            onChange={(e) => setFilterTime(e.target.value)}
            className="bg-navy-light border border-navy-accent/50 text-xs text-slate-300 rounded-lg p-2 hover:border-brand-cyan cursor-pointer focus:outline-none"
          >
            <option value="today">Today (Last 24h)</option>
            <option value="last_7_days">Last 7 Days</option>
            <option value="last_month">Last 30 Days</option>
          </select>
          <Button variant="outline" size="sm" onClick={() => handleExport("csv")}>
            📥 Export CSV
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport("xlsx")}>
            📥 Export Excel
          </Button>
          <Button variant="outline" size="sm" onClick={fetchAnalytics}>
            🔄 Refresh
          </Button>
        </div>
      </PageHeader>

      {categories.length === 0 && vehicleTypes.length === 0 ? (
        <EmptyState
          title="No Analytics Data Available"
          description="Populate the violations registry with detections to compile analytical models."
          icon={<span>📊</span>}
          action={<Button variant="outline" size="sm" onClick={fetchAnalytics}>Refresh Chart Console</Button>}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 1. Violation Distribution (Bar Chart) */}
          <Card>
            <CardHeader>
              <CardTitle>Violations Categories Distribution</CardTitle>
            </CardHeader>
            <CardContent className="h-72 flex items-end justify-between px-6 pb-4 pt-8">
              {categories.map((c: any, idx: number) => {
                const maxCount = Math.max(...categories.map((item: any) => item.count), 1);
                const percent = (c.count / maxCount) * 80; // max 80% height

                return (
                  <div key={idx} className="flex flex-col items-center group w-12">
                    <div className="text-[10px] text-brand-cyan font-mono font-bold opacity-0 group-hover:opacity-100 transition-opacity mb-1">
                      {c.count}
                    </div>
                    <div
                      className="w-8 bg-gradient-to-t from-brand-blue to-brand-cyan rounded-t-md hover:from-brand-cyan hover:to-brand-cyan/80 transition-all duration-500"
                      style={{ height: `${Math.max(8, percent)}%` }}
                    />
                    <span className="text-[8px] text-slate-400 mt-2 rotate-45 origin-left whitespace-nowrap">
                      {c.type.split(" ")[0]}
                    </span>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* 2. Vehicle Types Distribution (Donut Chart) */}
          <Card>
            <CardHeader>
              <CardTitle>Vehicle Categories Ratio</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-around h-72">
              {/* Simple Custom SVG Pie segment representation */}
              <svg className="w-40 h-40 transform -rotate-90" viewBox="0 0 32 32">
                <circle cx="16" cy="16" r="14" fill="transparent" stroke="#1e293b" strokeWidth="4" />
                {vehicleTypes.reduce(
                  (acc: any, item: any, idx: number) => {
                    const total = vehicleTypes.reduce((sum: number, cur: any) => sum + cur.value, 0) || 1;
                    const percent = (item.value / total) * 100;
                    const strokeDasharray = `${percent} ${100 - percent}`;
                    const strokeDashoffset = 100 - acc.currentOffset;

                    const colors = ["#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#3b82f6"];
                    const col = colors[idx % colors.length];

                    acc.elements.push(
                      <circle
                        key={idx}
                        cx="16"
                        cy="16"
                        r="14"
                        fill="transparent"
                        stroke={col}
                        strokeWidth="4"
                        strokeDasharray={strokeDasharray}
                        strokeDashoffset={strokeDashoffset}
                        pathLength="100"
                      />
                    );
                    acc.currentOffset += percent;
                    return acc;
                  },
                  { elements: [], currentOffset: 0 }
                ).elements}
              </svg>
              {/* Legend */}
              <div className="space-y-2 text-xs">
                {vehicleTypes.map((item: any, idx: number) => {
                  const colors = ["#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#3b82f6"];
                  const col = colors[idx % colors.length];
                  return (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: col }} />
                      <span className="text-slate-300 font-semibold">{item.name}:</span>
                      <span className="font-mono text-slate-400">{item.value}</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* 3. Monthly Trends (Line Graph) */}
          <Card>
            <CardHeader>
              <CardTitle>Historical Monthly Violations</CardTitle>
            </CardHeader>
            <CardContent className="h-72 flex items-end justify-between px-8 pb-4 pt-8">
              {monthlyTrends.map((item: any, idx: number) => {
                const maxViol = Math.max(...monthlyTrends.map((m: any) => m.violations), 1);
                const percent = (item.violations / maxViol) * 75;

                return (
                  <div key={idx} className="flex flex-col items-center group w-14">
                    <div className="text-[10px] text-brand-orange font-mono font-bold opacity-0 group-hover:opacity-100 transition-opacity mb-1">
                      {item.violations}
                    </div>
                    <div
                      className="w-4 bg-brand-orange/20 border-t-2 border-brand-orange hover:bg-brand-orange/40 transition-colors duration-300 rounded-t-sm"
                      style={{ height: `${Math.max(6, percent)}%` }}
                    />
                    <span className="text-[10px] text-slate-400 mt-2 font-mono">{item.month}</span>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* 4. Peak Traffic Hours (Bar Graph) */}
          <Card>
            <CardHeader>
              <CardTitle>Peak Activity Violations Hour Distribution</CardTitle>
            </CardHeader>
            <CardContent className="h-72 flex items-end justify-between px-6 pb-4 pt-8">
              {hourlyTrends.map((item: any, idx: number) => {
                const maxCount = Math.max(...hourlyTrends.map((h: any) => h.violations), 1);
                const percent = (item.violations / maxCount) * 80;

                // Show only key hours labels to avoid clutter
                const showLabel = idx % 4 === 0;

                return (
                  <div key={idx} className="flex flex-col items-center group flex-1">
                    <div className="text-[8px] text-brand-cyan font-mono font-bold opacity-0 group-hover:opacity-100 transition-opacity absolute mb-14 bg-navy-darker px-1 rounded">
                      {item.violations}
                    </div>
                    <div
                      className="w-1.5 bg-brand-cyan rounded-t-sm group-hover:bg-brand-cyan/85 transition-colors"
                      style={{ height: `${Math.max(4, percent)}%` }}
                    />
                    <span className="text-[8px] text-slate-500 mt-2 font-mono h-3">
                      {showLabel ? item.hour : ""}
                    </span>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

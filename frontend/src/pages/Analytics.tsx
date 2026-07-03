import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import { BarChart3, Download, FileSpreadsheet, ShieldAlert, Zap, Hourglass, CheckSquare } from "lucide-react";

interface CategoryData {
  type: string
  count: number
  total_fines: number
}

interface VehicleShare {
  name: string
  value: number
}

interface HourlyTrend {
  hour: string
  violations: number
}

interface MonthlyTrend {
  month: string
  violations: number
  fines: number
}

interface AnalyticsCharts {
  categories: CategoryData[]
  vehicle_types: VehicleShare[]
  hourly_trends: HourlyTrend[]
  monthly_trends: MonthlyTrend[]
  detection_accuracy: number
}

// Fallback mock analytics data
const fallbackAnalytics: AnalyticsCharts = {
  categories: [
    { type: "Red Light Jump", count: 82, total_fines: 164000 },
    { type: "Wrong Lane Driving", count: 45, total_fines: 45000 },
    { type: "Overspeeding", count: 91, total_fines: 91000 },
    { type: "No Helmet", count: 30, total_fines: 15000 }
  ],
  vehicle_types: [
    { name: "Car", value: 120 },
    { name: "Motorcycle", value: 85 },
    { name: "Truck", value: 20 },
    { name: "Bus", value: 15 },
    { name: "Auto", value: 8 }
  ],
  hourly_trends: Array.from({ length: 24 }, (_, i) => ({
    hour: `${i.toString().padStart(2, "0")}:00`,
    violations: Math.floor(Math.random() * 20) + 5
  })),
  monthly_trends: [
    { month: "Feb", violations: 180, fines: 220000 },
    { month: "Mar", violations: 220, fines: 280000 },
    { month: "Apr", violations: 200, fines: 245000 },
    { month: "May", violations: 250, fines: 310000 },
    { month: "Jun", violations: 280, fines: 350000 },
    { month: "Jul", violations: 140, fines: 170000 }
  ],
  detection_accuracy: 94.2
};

export default function Analytics() {
  const { token } = useContext(AuthContext);
  const [data, setData] = useState<AnalyticsCharts | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [exporting, setExporting] = useState<boolean>(false);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/analytics/charts`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const chartsData = await res.json();
          setData(chartsData);
        } else {
          throw new Error("API Offline");
        }
      } catch (err) {
        console.warn("Using offline fallback mock charts data.");
        setData(fallbackAnalytics);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [token]);

  const handleExportSubmit = async (format: "csv" | "xlsx") => {
    setExporting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/analytics/export?format=${format}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `traffic_violations_report.${format === "csv" ? "csv" : "xlsx"}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        alert("Failed to compile export files.");
      }
    } catch (err) {
      console.warn("Exporting mock report files offline.");
      // Create empty mock CSV data blob download
      const mockCsvContent = "Violation ID,License Plate,Violation Type,Location,Timestamp,Fine Amount\n102,DL 3C AB 9081,Red Light Jump,Connaught Place,2026-07-02 10:12:00,2000\n101,MH 12 RN 4567,Overspeeding,Rajpath Circle,2026-07-02 09:12:00,1000";
      const blob = new Blob([mockCsvContent], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `traffic_violations_report_MOCK.${format === "csv" ? "csv" : "xlsx"}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 rounded bg-slate-200 dark:bg-slate-800"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-72 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
          <div className="h-72 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
        </div>
      </div>
    );
  }

  const { categories, hourly_trends, monthly_trends, detection_accuracy } = data;

  const totalFines = categories.reduce((sum, item) => sum + item.total_fines, 0);
  const totalViolations = categories.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Analytics Desk</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Audit system accuracy rates, fine collections charts, and violations distributions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => handleExportSubmit("csv")}
            disabled={exporting}
            variant="outline"
            size="sm"
            className="text-[10px]"
          >
            <Download size={12} className="mr-1.5" />
            Export CSV
          </Button>
          <Button
            onClick={() => handleExportSubmit("xlsx")}
            disabled={exporting}
            size="sm"
            className="text-[10px]"
          >
            <FileSpreadsheet size={12} className="mr-1.5" />
            Export Excel
          </Button>
        </div>
      </div>

      {/* Metrics widgets */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <Card className="glass-card flex items-center gap-4 p-5">
          <div className="h-10 w-10 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
            <Zap size={20} className="animate-pulse" />
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest block">AI Model Accuracy</span>
            <strong className="text-xl font-extrabold">{detection_accuracy}%</strong>
          </div>
        </Card>

        <Card className="glass-card flex items-center gap-4 p-5">
          <div className="h-10 w-10 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0">
            <Hourglass size={20} />
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest block">Accumulated Fines</span>
            <strong className="text-xl font-extrabold">₹{totalFines.toLocaleString()}</strong>
          </div>
        </Card>

        <Card className="glass-card flex items-center gap-4 p-5">
          <div className="h-10 w-10 rounded-xl bg-indigo-500/10 text-indigo-500 flex items-center justify-center shrink-0">
            <CheckSquare size={20} />
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest block">Monitored Violations</span>
            <strong className="text-xl font-extrabold">{totalViolations}</strong>
          </div>
        </Card>
      </div>

      {/* Grid of charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Hourly Peak Infractions */}
        <Card className="glass-card p-6 space-y-4">
          <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <BarChart3 size={16} className="text-blue-500" />
            Peak Hours Violation Distribution
          </CardTitle>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={hourly_trends} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                <XAxis dataKey="hour" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '10px' }} />
                <Line type="monotone" dataKey="violations" stroke="#3b82f6" strokeWidth={2.5} dot={false} name="Violations" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Monthly Fine Amount */}
        <Card className="glass-card p-6 space-y-4">
          <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <BarChart3 size={16} className="text-emerald-500" />
            Monthly Fine Collections (₹)
          </CardTitle>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthly_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '10px' }} />
                <Bar dataKey="fines" fill="#10b981" radius={[4, 4, 0, 0]} name="Fines (₹)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Categories Bar Chart */}
        <Card className="glass-card p-6 space-y-4 lg:col-span-2">
          <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <ShieldAlert size={16} className="text-red-500" />
            Violation Categories Breakdown
          </CardTitle>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={categories}
                layout="vertical"
                margin={{ top: 10, right: 10, left: 10, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#1e293b" className="hidden dark:block" />
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" className="dark:hidden" />
                <XAxis type="number" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <YAxis type="category" dataKey="type" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} width={120} />
                <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '10px' }} />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} name="Count" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

      </div>
    </div>
  );
}

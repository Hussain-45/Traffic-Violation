import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";
import {
  BarChart3,
  Download,
  FileSpreadsheet,
  ShieldAlert,
  Zap,
  Hourglass,
  CheckSquare,
  Clock,
  Printer,
  TrendingUp,
  Map,
  Flame,
  AlertTriangle
} from "lucide-react";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

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

interface DailyTrend {
  day: string
  violations: number
}

interface MonthlyTrend {
  month: string
  violations: number
  fines: number
}

interface ViolationTrendCompare {
  date: string
  overspeeding: number
  red_light: number
  wrong_lane: number
}

interface HeatmapSector {
  sector: string
  camera_count: number
  risk_level: "High" | "Medium" | "Low"
  daily_incidents: number
  risk_score: number // 0-100
}

interface AnalyticsCharts {
  categories: CategoryData[]
  vehicle_types: VehicleShare[]
  hourly_trends: HourlyTrend[]
  daily_trends: DailyTrend[]
  monthly_trends: MonthlyTrend[]
  violation_trends: ViolationTrendCompare[]
  heatmap_sectors: HeatmapSector[]
  detection_accuracy: number
}

// Full mock analytics dataset
const fallbackAnalytics: AnalyticsCharts = {
  categories: [
    { type: "Red Light Jump", count: 82, total_fines: 164000 },
    { type: "Wrong Lane Driving", count: 45, total_fines: 45000 },
    { type: "Overspeeding", count: 91, total_fines: 91000 },
    { type: "No Helmet", count: 30, total_fines: 15000 },
    { type: "Triple Riding", count: 18, total_fines: 18000 }
  ],
  vehicle_types: [
    { name: "Car", value: 120 },
    { name: "Motorcycle", value: 85 },
    { name: "Truck", value: 20 },
    { name: "Bus", value: 15 },
    { name: "Auto", value: 48 }
  ],
  hourly_trends: [
    { hour: "08:00", violations: 12 },
    { hour: "10:00", violations: 24 },
    { hour: "12:00", violations: 18 },
    { hour: "14:00", violations: 15 },
    { hour: "16:00", violations: 29 },
    { hour: "18:00", violations: 38 },
    { hour: "20:00", violations: 22 },
    { hour: "22:00", violations: 11 }
  ],
  daily_trends: [
    { day: "Mon", violations: 22 },
    { day: "Tue", violations: 29 },
    { day: "Wed", violations: 35 },
    { day: "Thu", violations: 24 },
    { day: "Fri", violations: 42 },
    { day: "Sat", violations: 51 },
    { day: "Sun", violations: 30 }
  ],
  monthly_trends: [
    { month: "Jan", violations: 120, fines: 150000 },
    { month: "Feb", violations: 180, fines: 220000 },
    { month: "Mar", violations: 220, fines: 280000 },
    { month: "Apr", violations: 200, fines: 245000 },
    { month: "May", violations: 250, fines: 310000 },
    { month: "Jun", violations: 280, fines: 350000 }
  ],
  violation_trends: [
    { date: "06/25", overspeeding: 12, red_light: 8, wrong_lane: 4 },
    { date: "06/26", overspeeding: 18, red_light: 10, wrong_lane: 5 },
    { date: "06/27", overspeeding: 15, red_light: 12, wrong_lane: 6 },
    { date: "06/28", overspeeding: 22, red_light: 9, wrong_lane: 3 },
    { date: "06/29", overspeeding: 25, red_light: 15, wrong_lane: 8 },
    { date: "06/30", overspeeding: 31, red_light: 19, wrong_lane: 11 }
  ],
  heatmap_sectors: [
    { sector: "Connaught Place Sector 1", camera_count: 5, risk_level: "High", daily_incidents: 24, risk_score: 85 },
    { sector: "India Gate Circular Radial", camera_count: 3, risk_level: "Medium", daily_incidents: 12, risk_score: 55 },
    { sector: "Rajouri Garden Crossing", camera_count: 4, risk_level: "Medium", daily_incidents: 15, risk_score: 62 },
    { sector: "AIIMS Ring Road Flyover", camera_count: 6, risk_level: "High", daily_incidents: 32, risk_score: 92 },
    { sector: "Karol Bagh Bazar Market", camera_count: 2, risk_level: "Low", daily_incidents: 5, risk_score: 28 }
  ],
  detection_accuracy: 94.6
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
        a.download = `traffic_violations_analytics.${format === "csv" ? "csv" : "xlsx"}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        alert("Failed to compile export files.");
      }
    } catch (err) {
      console.warn("Exporting mock report files offline.");
      const mockCsvContent = "Violation ID,License Plate,Violation Type,Location,Timestamp,Fine Amount\n102,DL 3C AB 9081,Red Light Jump,Connaught Place,2026-07-02 10:12:00,2000\n101,MH 12 RN 4567,Overspeeding,Rajpath Circle,2026-07-02 09:12:00,1000";
      const blob = new Blob([mockCsvContent], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `traffic_violations_analytics_MOCK.${format === "csv" ? "csv" : "xlsx"}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading || !data) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 rounded bg-slate-200 dark:bg-slate-800"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-28 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
          <div className="h-28 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
          <div className="h-28 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
        </div>
      </div>
    );
  }

  const {
    categories,
    vehicle_types,
    hourly_trends,
    daily_trends,
    monthly_trends,
    violation_trends,
    heatmap_sectors,
    detection_accuracy
  } = data;

  const totalFines = categories.reduce((sum, item) => sum + item.total_fines, 0);
  const totalViolations = categories.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="space-y-6 print:p-0">
      
      {/* Header and Export Tools */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Analytics Desk</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
            Audit system accuracy rates, spatial heatmaps, peak hours, and fine collections.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            onClick={handlePrint}
            variant="outline"
            size="sm"
            className="text-[10px] h-9 font-bold"
          >
            <Printer size={12} className="mr-1.5" />
            Print Report (PDF)
          </Button>
          <Button
            onClick={() => handleExportSubmit("csv")}
            disabled={exporting}
            variant="outline"
            size="sm"
            className="text-[10px] h-9 font-bold"
          >
            <Download size={12} className="mr-1.5" />
            CSV Data
          </Button>
          <Button
            onClick={() => handleExportSubmit("xlsx")}
            disabled={exporting}
            size="sm"
            className="text-[10px] h-9 font-bold"
          >
            <FileSpreadsheet size={12} className="mr-1.5" />
            Excel Report
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <Card className="glass-card flex items-center gap-4 p-5">
          <div className="h-10 w-10 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
            <Zap size={20} className="animate-pulse" />
          </div>
          <div>
            <span className="text-[10px] text-slate-450 font-bold uppercase tracking-widest block">AI Model Accuracy</span>
            <strong className="text-xl font-extrabold text-slate-800 dark:text-slate-100">{detection_accuracy}%</strong>
          </div>
        </Card>

        <Card className="glass-card flex items-center gap-4 p-5">
          <div className="h-10 w-10 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center shrink-0">
            <Hourglass size={20} />
          </div>
          <div>
            <span className="text-[10px] text-slate-450 font-bold uppercase tracking-widest block">Accumulated Fines</span>
            <strong className="text-xl font-extrabold text-slate-800 dark:text-slate-100">₹{totalFines.toLocaleString()}</strong>
          </div>
        </Card>

        <Card className="glass-card flex items-center gap-4 p-5">
          <div className="h-10 w-10 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0">
            <CheckSquare size={20} />
          </div>
          <div>
            <span className="text-[10px] text-slate-450 font-bold uppercase tracking-widest block">Monitored Violations</span>
            <strong className="text-xl font-extrabold text-slate-800 dark:text-slate-100">{totalViolations}</strong>
          </div>
        </Card>
      </div>

      {/* Tabbed Chart Layout */}
      <Tabs defaultValue="telemetry" className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-6 print:hidden">
          <TabsTrigger value="telemetry" className="text-xs font-bold py-2">
            Violations Telemetry
          </TabsTrigger>
          <TabsTrigger value="financials" className="text-xs font-bold py-2">
            Financials & Categories
          </TabsTrigger>
          <TabsTrigger value="spatial" className="text-xs font-bold py-2">
            Spatial Heatmaps
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Violations Telemetry (Daily, Monthly, Peak, Trends) */}
        <TabsContent value="telemetry" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* 1. Daily Violations (Area Chart) */}
            <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm">
              <CardHeader className="p-0 pb-4">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <TrendingUp size={15} className="text-blue-500" />
                  Daily Violations
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Offences recorded daily over the past week.
                </CardDescription>
              </CardHeader>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={daily_trends} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorDailyViol" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                    <XAxis dataKey="day" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px', border: 'none' }} />
                    <Area type="monotone" dataKey="violations" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorDailyViol)" name="Violations" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* 2. Monthly Violations (Line Chart) */}
            <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm">
              <CardHeader className="p-0 pb-4">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <TrendingUp size={15} className="text-emerald-500" />
                  Monthly Violations
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Log of total offences recorded month-by-month.
                </CardDescription>
              </CardHeader>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={monthly_trends} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                    <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px', border: 'none' }} />
                    <Line type="monotone" dataKey="violations" stroke="#10b981" strokeWidth={2} name="Violations" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* 3. Peak Hours (Bar Chart) */}
            <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm">
              <CardHeader className="p-0 pb-4">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Clock size={15} className="text-amber-500" />
                  Peak Hours Distribution
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Average violations logged grouped by hour of the day.
                </CardDescription>
              </CardHeader>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hourly_trends} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                    <XAxis dataKey="hour" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px', border: 'none' }} />
                    <Bar dataKey="violations" fill="#f59e0b" radius={[3, 3, 0, 0]} name="Violations" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* 4. Violation Trends Compare (Multi-Line Chart) */}
            <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm">
              <CardHeader className="p-0 pb-4">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <TrendingUp size={15} className="text-indigo-500" />
                  Violation Type Trends
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Comparing overspeeding, red light jumps, and lane infractions over time.
                </CardDescription>
              </CardHeader>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={violation_trends} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                    <XAxis dataKey="date" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px', border: 'none' }} />
                    <Legend wrapperStyle={{ fontSize: '8px', fontWeight: 'bold' }} />
                    <Line type="monotone" dataKey="overspeeding" stroke="#3b82f6" strokeWidth={2} name="Overspeeding" />
                    <Line type="monotone" dataKey="red_light" stroke="#ef4444" strokeWidth={2} name="Red Light" />
                    <Line type="monotone" dataKey="wrong_lane" stroke="#f59e0b" strokeWidth={2} name="Wrong Lane" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

          </div>
        </TabsContent>

        {/* Tab 2: Financials & Categories */}
        <TabsContent value="financials" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* 5. Fine Collection (Bar Chart) */}
            <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm">
              <CardHeader className="p-0 pb-4">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Hourglass size={15} className="text-emerald-500" />
                  Monthly Fine Collections (₹)
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Total tariff revenue values logged over months.
                </CardDescription>
              </CardHeader>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthly_trends} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                    <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px', border: 'none' }} />
                    <Bar dataKey="fines" fill="#10b981" radius={[4, 4, 0, 0]} name="Collections (₹)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* 6. Vehicle Types (Donut Chart) */}
            <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm flex flex-col justify-between">
              <CardHeader className="p-0 pb-2">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Vehicle Types Ratio
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Distribution of monitored vehicle categories committing infractions.
                </CardDescription>
              </CardHeader>
              <div className="h-44 relative flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={vehicle_types}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={65}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {vehicle_types.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: '8px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px' }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute flex flex-col items-center justify-center">
                  <span className="text-lg font-extrabold text-slate-800 dark:text-slate-100">
                    {vehicle_types.reduce((sum, item) => sum + item.value, 0)}
                  </span>
                  <span className="text-[8px] text-slate-400 font-bold uppercase tracking-wider">Vehicles</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-x-2.5 gap-y-1 justify-center text-[9px] font-bold mt-2">
                {vehicle_types.map((entry, index) => (
                  <div key={entry.name} className="flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
                    <span className="text-slate-500 dark:text-slate-400">{entry.name}</span>
                    <span className="text-slate-800 dark:text-slate-200">({entry.value})</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Violation breakdown */}
            <Card className="glass-card p-6 space-y-4 lg:col-span-2">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <ShieldAlert size={15} className="text-red-500" />
                Categories breakdown
              </CardTitle>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={categories} layout="vertical" margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#1e293b" className="hidden dark:block" />
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" className="dark:hidden" />
                    <XAxis type="number" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                    <YAxis type="category" dataKey="type" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} width={120} />
                    <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px', border: 'none' }} />
                    <Bar dataKey="count" fill="#ef4444" radius={[0, 4, 4, 0]} name="Count" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

          </div>
        </TabsContent>

        {/* Tab 3: Spatial Heatmap */}
        <TabsContent value="spatial" className="space-y-6">
          
          {/* 7. Sector Danger Heatmap Grid */}
          <Card className="glass-card p-6 space-y-4">
            <CardHeader className="p-0">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Map size={16} className="text-red-500 animate-pulse" />
                Junction Risk Heatmap Grid
              </CardTitle>
              <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                Danger diagnostics indicating camera nodes, incident rates, and safety scores.
              </CardDescription>
            </CardHeader>
            
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              {heatmap_sectors.map((item, idx) => {
                const isHigh = item.risk_level === "High";
                const isMed = item.risk_level === "Medium";
                
                return (
                  <Card
                    key={idx}
                    className={`p-5 rounded-2xl border flex flex-col justify-between gap-4 relative overflow-hidden group hover:scale-102 transition-transform duration-300 ${
                      isHigh
                        ? "border-red-500/30 bg-red-650/5"
                        : isMed
                        ? "border-amber-500/20 bg-amber-650/5"
                        : "border-emerald-500/10 bg-emerald-650/5"
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-slate-450 uppercase">Risk Level</span>
                        <Badge
                          variant={isHigh ? "destructive" : isMed ? "secondary" : "success"}
                          className="text-[8px] font-extrabold uppercase py-0 px-2"
                        >
                          {item.risk_level}
                        </Badge>
                      </div>

                      <div>
                        <h4 className="font-extrabold text-xs text-slate-800 dark:text-slate-100">{item.sector}</h4>
                        <span className="text-[9px] text-slate-450 font-bold block mt-1">Cameras Active: {item.camera_count}</span>
                      </div>
                    </div>

                    <div className="space-y-2 border-t border-slate-200/40 dark:border-slate-850/40 pt-3 text-[10px] font-semibold text-slate-500">
                      <div className="flex justify-between">
                        <span>Daily Incidents</span>
                        <strong className="text-slate-800 dark:text-slate-200">{item.daily_incidents} logs</strong>
                      </div>

                      {/* Danger scale strip */}
                      <div className="space-y-1">
                        <div className="flex justify-between text-[9px] font-bold">
                          <span>Danger Index Score</span>
                          <span className={isHigh ? "text-red-500" : isMed ? "text-amber-500" : "text-emerald-500"}>
                            {item.risk_score} / 100
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-slate-200 dark:bg-slate-950 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              isHigh ? "bg-red-500" : isMed ? "bg-amber-500" : "bg-emerald-500"
                            }`}
                            style={{ width: `${item.risk_score}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          </Card>

        </TabsContent>
      </Tabs>

    </div>
  );
}

import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "../components/ui/table";
import { motion } from "framer-motion";
import { API_BASE_URL } from "../App";
import {
  TrendingUp,
  AlertTriangle,
  Car,
  Camera,
  Activity,
  Flame,
  Plus,
  Play,
  Clock,
  ExternalLink,
  MapPin,
  ShieldCheck,
  IndianRupee
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar
} from "recharts";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

interface SummaryStats {
  total_vehicles: number
  total_violations: number
  active_cameras: string
  todays_cases: number
}

interface DailyTrend {
  day: string
  count: number
}

interface MonthlyTrend {
  month: string
  count: number
}

interface TypeShare {
  name: string
  value: number
}

interface CollectionTrend {
  month: string
  collected: number
}

interface ActivityRecord {
  id: number
  plate: string
  type: string
  location: string
  timestamp: string
  fine_amount: number
  status: "pending" | "paid" | "resolved"
}

// Full mock data matching the cards and charts requirements
const mockSummary: SummaryStats = {
  total_vehicles: 1284,
  total_violations: 248,
  active_cameras: "4 / 5 Online",
  todays_cases: 18
};

const mockDailyViolations: DailyTrend[] = [
  { day: "Mon", count: 12 },
  { day: "Tue", count: 18 },
  { day: "Wed", count: 24 },
  { day: "Thu", count: 16 },
  { day: "Fri", count: 29 },
  { day: "Sat", count: 35 },
  { day: "Sun", count: 21 }
];

const mockMonthlyViolations: MonthlyTrend[] = [
  { month: "Jan", count: 120 },
  { month: "Feb", count: 180 },
  { month: "Mar", count: 220 },
  { month: "Apr", count: 195 },
  { month: "May", count: 250 },
  { month: "Jun", count: 280 }
];

const mockTypeDistribution: TypeShare[] = [
  { name: "Car", value: 450 },
  { name: "Motorcycle", value: 380 },
  { name: "Truck", value: 120 },
  { name: "Bus", value: 95 },
  { name: "Auto", value: 239 }
];

const mockFineCollections: CollectionTrend[] = [
  { month: "Jan", collected: 45000 },
  { month: "Feb", collected: 62000 },
  { month: "Mar", collected: 78000 },
  { month: "Apr", collected: 69000 },
  { month: "May", collected: 95000 },
  { month: "Jun", collected: 110000 }
];

const mockActivities: ActivityRecord[] = [
  { id: 105, plate: "DL 3C AW 9081", type: "Red Light Jump", location: "Connaught Place Jn 1", timestamp: "10:18 AM", fine_amount: 2000, status: "pending" },
  { id: 104, plate: "MH 12 RN 4567", type: "Overspeeding", location: "India Gate Circular 3", timestamp: "09:42 AM", fine_amount: 1000, status: "paid" },
  { id: 103, plate: "KA 05 XY 5678", type: "No Helmet", location: "Rajouri Garden Flyover", timestamp: "09:05 AM", fine_amount: 500, status: "pending" },
  { id: 102, plate: "HR 26 AZ 1212", type: "Wrong Lane Driving", location: "AIIMS Crossing Main Feed", timestamp: "08:15 AM", fine_amount: 1000, status: "resolved" },
  { id: 101, plate: "UP 16 PQ 8890", type: "Triple Riding", location: "Karol Bagh Bazar CCTV 3", timestamp: "07:30 AM", fine_amount: 1000, status: "pending" }
];

const PLATES_POOL = ["DL 3C MX 9821", "MH 14 BN 2290", "KA 03 FG 1156", "HR 26 AZ 4545", "UP 16 KL 8890"];
const LOCATIONS_POOL = ["Connaught Place Jn 1", "India Gate Circular 3", "Rajouri Garden Flyover", "AIIMS Crossing Main Feed", "Karol Bagh Bazar CCTV 3"];
const VIOLATIONS_POOL = [
  { type: "Red Light Jump", amount: 2000 },
  { type: "Overspeeding", amount: 1000 },
  { type: "No Helmet", amount: 500 },
  { type: "Wrong Lane Driving", amount: 1000 }
];

export default function Dashboard() {
  const [summary, setSummary] = useState<SummaryStats>(mockSummary);
  const [activities, setActivities] = useState<ActivityRecord[]>(mockActivities);
  
  const [sysResources, setSysResources] = useState({
    cpu: 21.4,
    ram: 44.1,
    gpu_available: false,
    gpu: 0.0,
    disk: 44.5,
    threads: 12
  });

  useEffect(() => {
    const fetchResources = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/dashboard/system-health`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
        });
        if (response.ok) {
          const data = await response.json();
          setSysResources(data);
        }
      } catch (err) {
        // Fallback simulation updates
        setSysResources((prev) => ({
          ...prev,
          cpu: Math.floor(Math.random() * 10) + 15,
          ram: Math.floor(Math.random() * 5) + 40,
          threads: Math.floor(Math.random() * 4) + 10
        }));
      }
    };

    fetchResources();
    const interval = setInterval(fetchResources, 5000);
    return () => clearInterval(interval);
  }, []);

  const triggerSimulatedIncident = () => {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const randomPlate = PLATES_POOL[Math.floor(Math.random() * PLATES_POOL.length)];
    const randomLoc = LOCATIONS_POOL[Math.floor(Math.random() * LOCATIONS_POOL.length)];
    const randomOffence = VIOLATIONS_POOL[Math.floor(Math.random() * VIOLATIONS_POOL.length)];

    const newRecord: ActivityRecord = {
      id: Math.floor(Math.random() * 900) + 200,
      plate: randomPlate,
      type: randomOffence.type,
      location: randomLoc,
      timestamp: timeStr,
      fine_amount: randomOffence.amount,
      status: "pending"
    };

    setActivities((prev) => [newRecord, ...prev.slice(0, 4)]);
    setSummary((prev) => ({
      ...prev,
      total_vehicles: prev.total_vehicles + 1,
      total_violations: prev.total_violations + 1,
      todays_cases: prev.todays_cases + 1
    }));
  };

  return (
    <div className="space-y-6">
      
      {/* Header & Simulator Panel */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Smart City Command Centre</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
            AI-powered traffic violation metrics and monitoring system.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <Link to="/upload">
            <Button variant="outline" size="sm" className="text-[10px] h-9 font-bold">
              <Plus size={12} className="mr-1" /> Scan Media
            </Button>
          </Link>
          <Link to="/live">
            <Button variant="secondary" size="sm" className="text-[10px] h-9 font-bold">
              <Play size={12} className="mr-1" /> Live Monitor
            </Button>
          </Link>
          <Button
            onClick={triggerSimulatedIncident}
            size="sm"
            className="text-[10px] h-9 bg-red-650 hover:bg-red-500 text-white font-extrabold shadow-md shadow-red-500/20"
          >
            <Flame size={12} className="mr-1 animate-pulse" /> Simulate Incident
          </Button>
        </div>
      </div>

      {/* 4 Dashboard Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        
        {/* Total Vehicles */}
        <Card className="glass-card flex items-center justify-between p-6 relative overflow-hidden group hover:border-blue-500/30 transition-all duration-300">
          <div className="space-y-1.5 z-10">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Total Vehicles</span>
            <h3 className="text-2xl font-extrabold tracking-tight">{summary.total_vehicles.toLocaleString()}</h3>
            <span className="text-[9px] font-bold text-blue-500 flex items-center gap-1">
              <TrendingUp size={10} /> +12% logs vs yesterday
            </span>
          </div>
          <div className="h-12 w-12 rounded-2xl bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
            <Car size={22} />
          </div>
        </Card>

        {/* Total Violations */}
        <Card className="glass-card flex items-center justify-between p-6 relative overflow-hidden group hover:border-red-500/30 transition-all duration-300">
          <div className="space-y-1.5 z-10">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Total Violations</span>
            <h3 className="text-2xl font-extrabold tracking-tight text-red-500">{summary.total_violations}</h3>
            <span className="text-[9px] font-bold text-red-500 flex items-center gap-1">
              <AlertTriangle size={10} /> Cumulative offences
            </span>
          </div>
          <div className="h-12 w-12 rounded-2xl bg-red-500/10 text-red-500 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
            <AlertTriangle size={22} />
          </div>
        </Card>

        {/* Active Cameras */}
        <Card className="glass-card flex items-center justify-between p-6 relative overflow-hidden group hover:border-emerald-500/30 transition-all duration-300">
          <div className="space-y-1.5 z-10">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Active Cameras</span>
            <h3 className="text-2xl font-extrabold tracking-tight text-emerald-500">{summary.active_cameras}</h3>
            <span className="text-[9px] font-bold text-emerald-500 flex items-center gap-1">
              <ShieldCheck size={10} /> Node networks active
            </span>
          </div>
          <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
            <Camera size={22} />
          </div>
        </Card>

        {/* Today's Cases */}
        <Card className="glass-card flex items-center justify-between p-6 relative overflow-hidden group hover:border-amber-500/30 transition-all duration-300">
          <div className="space-y-1.5 z-10">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Today's Cases</span>
            <h3 className="text-2xl font-extrabold tracking-tight text-amber-500">{summary.todays_cases}</h3>
            <span className="text-[9px] font-bold text-amber-500 flex items-center gap-1">
              <Activity size={10} className="animate-pulse" /> Live traffic incidents
            </span>
          </div>
          <div className="h-12 w-12 rounded-2xl bg-amber-500/10 text-amber-500 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
            <Activity size={22} />
          </div>
        </Card>
      </div>

      {/* 4 Charts Grid (2 columns on lg+) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        
        {/* 1. Daily Violations (Area Chart) */}
        <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm">
          <div className="space-y-1.5 pb-2">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <TrendingUp size={16} className="text-blue-500" />
              Daily Violations
            </CardTitle>
            <CardDescription className="text-[10px] text-slate-500">
              Offences recorded daily over the past week.
            </CardDescription>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mockDailyViolations} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorDaily" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                <XAxis dataKey="day" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px', border: 'none' }} />
                <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorDaily)" name="Violations" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* 2. Monthly Violations (Line Chart) */}
        <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm">
          <div className="space-y-1.5 pb-2">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <TrendingUp size={16} className="text-emerald-500" />
              Monthly Violations
            </CardTitle>
            <CardDescription className="text-[10px] text-slate-500">
              Total offences tracked over months.
            </CardDescription>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockMonthlyViolations} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px', border: 'none' }} />
                <Line type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2.5} activeDot={{ r: 6 }} name="Violations" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* 3. Vehicle Types (Donut Chart) */}
        <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm flex flex-col justify-between">
          <div className="space-y-1.5 pb-1">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Vehicle Types
            </CardTitle>
            <CardDescription className="text-[10px] text-slate-500">
              Distribution of monitored vehicle categories.
            </CardDescription>
          </div>
          <div className="h-44 relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={mockTypeDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={65}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {mockTypeDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-lg font-extrabold">{summary.total_vehicles}</span>
              <span className="text-[8px] text-slate-400 font-bold uppercase tracking-wider">Monitored</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-x-2 gap-y-1 justify-center text-[9px] font-bold mt-2">
            {mockTypeDistribution.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
                <span className="text-slate-500 dark:text-slate-400">{entry.name}</span>
                <span className="text-slate-800 dark:text-slate-200">({entry.value})</span>
              </div>
            ))}
          </div>
        </Card>

        {/* 4. Fine Collection (Bar Chart) */}
        <Card className="glass-card p-6 min-w-0 overflow-hidden shadow-sm">
          <div className="space-y-1.5 pb-2">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <IndianRupee size={16} className="text-amber-500" />
              Fine Collection
            </CardTitle>
            <CardDescription className="text-[10px] text-slate-500">
              Total tariff collection values logged over months (₹).
            </CardDescription>
          </div>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockFineCollections} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block" />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden" />
                <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px', border: 'none' }} />
                <Bar dataKey="collected" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Fines Collected (₹)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

      </div>

      {/* Bottom Grid: Recent Activity & System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column (Recent Activity Table) */}
        <div className="lg:col-span-2">
          <Card className="glass-card shadow-sm overflow-hidden p-0 h-full">
            <CardHeader className="p-5 border-b border-slate-200/40 dark:border-slate-850/40 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Recent Activity logs
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-550 mt-0.5">
                  Latest AI detection events recorded across city networks.
                </CardDescription>
              </div>
              <Link to="/violations">
                <Button variant="ghost" size="sm" className="text-[10px] font-bold text-blue-500 flex items-center gap-1">
                  Violations Registry <ExternalLink size={12} />
                </Button>
              </Link>
            </CardHeader>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Incident</TableHead>
                  <TableHead>License Plate</TableHead>
                  <TableHead>Violation Type</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Fine Tariff</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activities.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-bold text-slate-455">#{item.id}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-none font-bold text-[9px] py-0.5 px-2">
                        {item.plate}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-extrabold text-slate-700 dark:text-slate-200 text-xs">
                      {item.type}
                    </TableCell>
                    <TableCell className="text-slate-555 font-semibold flex items-center gap-1 mt-2.5">
                      <MapPin size={10} className="shrink-0 text-slate-400" />
                      {item.location}
                    </TableCell>
                    <TableCell className="text-slate-400 text-[10px]">{item.timestamp}</TableCell>
                    <TableCell className="font-extrabold text-slate-800 dark:text-slate-100">
                      ₹{item.fine_amount.toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant={item.status === "paid" ? "success" : item.status === "resolved" ? "secondary" : "destructive"} className="text-[8px] py-0 px-2 font-bold">
                        {item.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </div>

        {/* Right Column (System Health Dashboard) */}
        <div className="lg:col-span-1">
          <Card className="glass-card p-5 h-full space-y-4 border-blue-500/10 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-xl pointer-events-none"></div>
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Activity size={15} className="text-blue-500 animate-pulse" />
                System Health
              </span>
              <Badge variant="outline" className="text-[8px] border-emerald-500/30 text-emerald-550 font-bold py-0.5 animate-pulse text-emerald-400">
                ONLINE
              </Badge>
            </CardTitle>
            
            <div className="space-y-4 text-xs font-semibold mt-3 text-slate-800 dark:text-slate-200">
              {/* CPU Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[10px]">
                  <span className="text-slate-450 uppercase font-bold">CPU Usage</span>
                  <strong className="text-slate-800 dark:text-slate-100">{sysResources.cpu}%</strong>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-900 rounded-full h-1.5 overflow-hidden">
                  <div className="bg-blue-500 h-full rounded-full transition-all duration-500" style={{ width: `${sysResources.cpu}%` }}></div>
                </div>
              </div>

              {/* RAM Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[10px]">
                  <span className="text-slate-450 uppercase font-bold">RAM Usage</span>
                  <strong className="text-slate-800 dark:text-slate-100">{sysResources.ram}%</strong>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-900 rounded-full h-1.5 overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full transition-all duration-500" style={{ width: `${sysResources.ram}%` }}></div>
                </div>
              </div>

              {/* GPU Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[10px]">
                  <span className="text-slate-450 uppercase font-bold">GPU Load (PyTorch CUDA)</span>
                  <strong className="text-slate-800 dark:text-slate-100">
                    {sysResources.gpu_available ? `${sysResources.gpu}%` : 'Not Available (CPU mode)'}
                  </strong>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-900 rounded-full h-1.5 overflow-hidden">
                  <div className="bg-purple-500 h-full rounded-full transition-all duration-500" style={{ width: `${sysResources.gpu_available ? sysResources.gpu : 0}%` }}></div>
                </div>
              </div>

              {/* Disk Progress Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[10px]">
                  <span className="text-slate-455 uppercase font-bold">Disk Space Usage</span>
                  <strong className="text-slate-800 dark:text-slate-100">{sysResources.disk}%</strong>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-900 rounded-full h-1.5 overflow-hidden">
                  <div className="bg-amber-500 h-full rounded-full transition-all duration-500" style={{ width: `${sysResources.disk}%` }}></div>
                </div>
              </div>

              {/* Active Threads Counter */}
              <div className="flex justify-between items-center pt-2 border-t border-slate-200/40 dark:border-slate-850/40 mt-1">
                <span className="text-slate-455 uppercase text-[9px] font-bold">Active Threads</span>
                <span className="text-slate-700 dark:text-slate-300 font-mono text-[11px] font-extrabold">{sysResources.threads} threads</span>
              </div>
            </div>
          </Card>
        </div>

      </div>

    </div>
  );
}

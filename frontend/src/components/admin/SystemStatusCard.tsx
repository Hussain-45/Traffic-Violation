import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/Card";

interface SystemStatusProps {
  statusData: {
    cpu_percent: number;
    memory_percent: number;
    memory_used_gb: number;
    memory_total_gb: number;
    disk_percent: number;
    disk_used_gb: number;
    disk_total_gb: number;
    uptime_seconds: number;
    api_status: string;
  };
  healthData?: {
    database: boolean;
    system_resources: boolean;
    api_health: boolean;
  };
}

export function SystemStatusCard({ statusData, healthData }: SystemStatusProps) {
  const formatUptime = (secs: number) => {
    const d = Math.floor(secs / (3600 * 24));
    const h = Math.floor((secs % (3600 * 24)) / 3600);
    const m = Math.floor((secs % 3600) / 60);
    return `${d}d ${h}h ${m}m`;
  };

  const getProgressColor = (percent: number) => {
    if (percent > 85) return "bg-status-red shadow-status-red/30";
    if (percent > 65) return "bg-amber-500 shadow-amber-500/30";
    return "bg-brand-cyan shadow-brand-cyan/30";
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* CPU Utilization */}
      <Card className="hover:border-brand-cyan/30 transition-all duration-300">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>CPU Load</CardTitle>
            <span className="text-xs font-mono text-brand-cyan bg-brand-cyan/10 px-2 py-0.5 rounded">
              {statusData.cpu_percent}%
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-2 w-full bg-navy-accent rounded-full overflow-hidden mb-3">
            <div
              className={`h-full rounded-full transition-all duration-500 ${getProgressColor(statusData.cpu_percent)}`}
              style={{ width: `${statusData.cpu_percent}%` }}
            />
          </div>
          <span className="text-xs text-slate-400">Total processor core load.</span>
        </CardContent>
      </Card>

      {/* Memory Utilization */}
      <Card className="hover:border-brand-cyan/30 transition-all duration-300">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>RAM Usage</CardTitle>
            <span className="text-xs font-mono text-brand-blue bg-brand-blue/10 px-2 py-0.5 rounded">
              {statusData.memory_percent}%
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-2 w-full bg-navy-accent rounded-full overflow-hidden mb-3">
            <div
              className={`h-full rounded-full transition-all duration-500 ${getProgressColor(statusData.memory_percent)}`}
              style={{ width: `${statusData.memory_percent}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Used: {statusData.memory_used_gb} GB</span>
            <span>Total: {statusData.memory_total_gb} GB</span>
          </div>
        </CardContent>
      </Card>

      {/* Storage Disk Space */}
      <Card className="hover:border-brand-cyan/30 transition-all duration-300">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Disk Space</CardTitle>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              {statusData.disk_percent}%
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-2 w-full bg-navy-accent rounded-full overflow-hidden mb-3">
            <div
              className={`h-full rounded-full transition-all duration-500 ${getProgressColor(statusData.disk_percent)}`}
              style={{ width: `${statusData.disk_percent}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Used: {statusData.disk_used_gb} GB</span>
            <span>Total: {statusData.disk_total_gb} GB</span>
          </div>
        </CardContent>
      </Card>

      {/* Diagnostic Health states */}
      <div className="md:col-span-3 grid grid-cols-1 sm:grid-cols-4 gap-5">
        <div className="p-4 bg-navy-light rounded-lg border border-navy-accent/50 flex flex-col justify-between">
          <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Uptime</span>
          <span className="text-xl font-bold mt-2 text-slate-200">{formatUptime(statusData.uptime_seconds)}</span>
        </div>
        <div className="p-4 bg-navy-light rounded-lg border border-navy-accent/50 flex flex-col justify-between">
          <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Database Link</span>
          <span className="flex items-center gap-2 mt-2">
            <span className={`w-2.5 h-2.5 rounded-full ${healthData?.database !== false ? 'bg-status-green animate-pulse' : 'bg-status-red'}`} />
            <span className="text-sm font-semibold">{healthData?.database !== false ? 'Connected' : 'Offline'}</span>
          </span>
        </div>
        <div className="p-4 bg-navy-light rounded-lg border border-navy-accent/50 flex flex-col justify-between">
          <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">API Gateways</span>
          <span className="flex items-center gap-2 mt-2">
            <span className={`w-2.5 h-2.5 rounded-full ${healthData?.api_health !== false ? 'bg-status-green animate-pulse' : 'bg-status-red'}`} />
            <span className="text-sm font-semibold">{healthData?.api_health !== false ? 'Healthy' : 'Error'}</span>
          </span>
        </div>
        <div className="p-4 bg-navy-light rounded-lg border border-navy-accent/50 flex flex-col justify-between">
          <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Resource Health</span>
          <span className="flex items-center gap-2 mt-2">
            <span className={`w-2.5 h-2.5 rounded-full ${healthData?.system_resources !== false ? 'bg-status-green animate-pulse' : 'bg-status-red'}`} />
            <span className="text-sm font-semibold">{healthData?.system_resources !== false ? 'Optimal' : 'Overloaded'}</span>
          </span>
        </div>
      </div>
    </div>
  );
}

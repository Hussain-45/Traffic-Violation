"use client";

import React from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatCard } from "@/components/ui/StatCard";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export default function Home() {
  return (
    <div>
      {/* Page Title & Actions */}
      <PageHeader
        title="Dashboard Overview"
        description="Monitor traffic status, active violation detections, and camera analytics feeds in real-time."
      >
        <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
          🔄 Refresh
        </Button>
        <Button variant="primary" size="sm" onClick={() => window.location.href = "/live"}>
          🎥 Live Feed
        </Button>
      </PageHeader>

      {/* Grid of Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5 mb-8">
        <StatCard
          title="Today's Violations"
          value="42"
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-5 h-5 text-status-red"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
              />
            </svg>
          }
          description="↗️ 12% increase from yesterday"
        />

        <StatCard
          title="Active Cameras"
          value="8 / 10"
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-5 h-5 text-brand-cyan"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6.827 6.175A2.31 2.31 0 0 1 5.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 0 0-1.134-.175 2.31 2.31 0 0 1-1.64-1.055l-.822-1.316a2.192 2.192 0 0 0-1.736-1.039 48.774 48.774 0 0 0-5.232 0 2.192 2.192 0 0 0-1.736 1.039l-.821 1.316Z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.5 12.75a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0ZM18.75 10.5h.008v.008h-.008V10.5Z"
              />
            </svg>
          }
          description="🟢 2 cameras offline for service"
        />

        <StatCard
          title="Vehicles Detected"
          value="1,842"
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-5 h-5 text-brand-blue"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.25 18.75a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 0 1-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124l-.318-5.085a3.375 3.375 0 0 0-3.064-3.166 48.704 48.704 0 0 0-10.955 0A3.375 3.375 0 0 0 4.066 12.91l-.317 5.085c-.04.62.47 1.124 1.09 1.124H6m12-4.5H6m12 0h-3m-3 0H6"
              />
            </svg>
          }
          description="↗️ 8.5% traffic volume increase"
        />

        <StatCard
          title="Emails Sent"
          value="36"
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-5 h-5 text-slate-300"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75"
              />
            </svg>
          }
          description="✅ 100% dispatch success rate"
        />

        <StatCard
          title="System Status"
          value="Operational"
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-5 h-5 text-status-green"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 15a4.5 4.5 0 0 0 4.5 4.5H18a3.75 3.75 0 0 0 1.332-7.257 3 3 0 0 0-3.758-3.848 5.25 5.25 0 0 0-10.233 2.33A4.502 4.502 0 0 0 2.25 15Z"
              />
            </svg>
          }
          description="🛡️ All services online"
        />
      </div>

      {/* Main Grid: Live Feed placeholder & Recent violations list */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Live feed placeholder */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Active Traffic Feed Tracker</CardTitle>
                <p className="text-xs text-slate-400 mt-1">Camera Node #01 - North Intersection Avenue</p>
              </div>
              <Badge variant="info">LIVE FEED</Badge>
            </CardHeader>
            <CardContent>
              {/* Simulated camera feed layout box */}
              <div className="aspect-video w-full rounded-lg bg-navy-dark border border-navy-accent/50 flex flex-col items-center justify-center relative overflow-hidden group">
                <div className="absolute inset-0 bg-radial-gradient from-transparent to-navy-darker/60 z-10 pointer-events-none"></div>
                
                {/* Simulated scan lines */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(18,24,36,0)_95%,rgba(0,0,0,0.3)_95%)] bg-[size:100%_15px] opacity-15 pointer-events-none"></div>

                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1}
                  stroke="currentColor"
                  className="w-16 h-16 text-slate-600 mb-3 animate-pulse"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z"
                  />
                </svg>
                <span className="text-sm font-semibold tracking-wider text-slate-400 uppercase select-none">
                  Camera Feed Offline
                </span>
                <span className="text-xs text-slate-500 mt-1.5 select-none">
                  Enable live feeds on the Live Monitoring tab.
                </span>

                {/* Simulated HUD elements */}
                <div className="absolute top-4 left-4 text-xs font-mono text-brand-cyan bg-navy-darker/80 px-2 py-1 rounded border border-navy-accent/50">
                  REC 🔴 FPS: 30
                </div>
                <div className="absolute top-4 right-4 text-xs font-mono text-slate-400 bg-navy-darker/80 px-2 py-1 rounded border border-navy-accent/50">
                  CAM_01_NORTH
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Recent violations */}
        <div>
          <Card className="h-full flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Recent Violations Log</CardTitle>
                <p className="text-xs text-slate-400 mt-1">Real-time detection events</p>
              </div>
              <Button variant="outline" size="sm" className="text-xs px-2.5 py-1" onClick={() => window.location.href = "/violations"}>
                View All
              </Button>
            </CardHeader>
            <CardContent className="flex-1 space-y-4 overflow-y-auto max-h-[350px]">
              {/* Dummy List of Violations */}
              {[
                { id: "1084", plate: "ABC-1234", type: "Red Light Jump", time: "2 min ago", severity: "danger" },
                { id: "1083", plate: "XYZ-9876", type: "No Helmet", time: "5 min ago", severity: "warning" },
                { id: "1082", plate: "KBL-5542", type: "Speed Limit Violation", time: "12 min ago", severity: "danger" },
                { id: "1081", plate: "TXR-3819", type: "Seat Belt Unfastened", time: "20 min ago", severity: "info" },
              ].map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-navy-dark/40 border border-navy-accent/20 hover:border-navy-accent/40 transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-slate-200 font-bold">{item.plate}</span>
                      <Badge variant={item.severity as any}>{item.type}</Badge>
                    </div>
                    <span className="text-[10px] text-slate-500 block">ID: #{item.id} • {item.time}</span>
                  </div>
                  <div className="w-8 h-8 rounded-lg bg-navy-accent/50 border border-navy-accent/30 flex items-center justify-center text-slate-400 font-bold text-xs select-none">
                    🖼️
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

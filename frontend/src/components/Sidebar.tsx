import React, { useContext } from "react";
import { Link, useLocation } from "react-router-dom";
import { AuthContext } from "../App";
import {
  LayoutDashboard,
  Radio,
  UploadCloud,
  AlertTriangle,
  BarChart3,
  Map as MapIcon,
  Camera,
  Users,
  Settings as SettingsIcon,
  ShieldCheck,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { cn } from "../lib/utils";

interface SidebarProps {
  isOpen: boolean
  setIsOpen: (isOpen: boolean) => void
}

export default function Sidebar({ isOpen, setIsOpen }: SidebarProps) {
  const { user } = useContext(AuthContext);
  const location = useLocation();

  const navItems = [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { name: "Live Feed", path: "/live", icon: Radio },
    { name: "Upload Engine", path: "/upload", icon: UploadCloud },
    { name: "Violations", path: "/violations", icon: AlertTriangle },
    { name: "Analytics", path: "/analytics", icon: BarChart3 },
    { name: "Heatmap Map", path: "/map", icon: MapIcon },
    { name: "CCTV Cameras", path: "/cameras", icon: Camera },
    { name: "User Management", path: "/users", icon: Users, adminOnly: true },
    { name: "System Settings", path: "/settings", icon: SettingsIcon },
  ];

  const filteredItems = navItems.filter(
    (item) => !item.adminOnly || user?.role === "admin"
  );

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen z-40 transition-all duration-300 border-r border-slate-200/50 bg-white/80 dark:border-slate-800/50 dark:bg-slate-950/80 backdrop-blur-md flex flex-col justify-between",
        isOpen ? "w-64" : "w-20"
      )}
    >
      <div>
        {/* Branding header */}
        <div className="flex items-center justify-between p-4 h-16 border-b border-slate-200/50 dark:border-slate-800/50">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-500/20">
              <ShieldCheck size={20} className="animate-pulse" />
            </div>
            {isOpen && (
              <div className="flex flex-col">
                <span className="font-bold tracking-wide text-xs bg-gradient-to-r from-blue-600 to-indigo-500 bg-clip-text text-transparent dark:from-blue-400 dark:to-indigo-300 uppercase">
                  TRAFFIC DETECT
                </span>
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">
                  Smart City Hub
                </span>
              </div>
            )}
          </div>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="hidden md:flex h-6 w-6 items-center justify-center rounded-md border border-slate-200 hover:bg-slate-100 text-slate-400 dark:border-slate-800 dark:hover:bg-slate-900 cursor-pointer"
          >
            {isOpen ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
          </button>
        </div>

        {/* Navigation List */}
        <nav className="p-3 space-y-1.5">
          {filteredItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center gap-4 px-3.5 py-3 rounded-xl transition-all duration-200 group font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100/50 dark:hover:bg-slate-900/60 dark:hover:text-slate-100",
                  {
                    "bg-blue-600 text-white hover:bg-blue-500 hover:text-white shadow-lg shadow-blue-500/20 dark:text-white": isActive,
                  }
                )}
              >
                <Icon
                  size={18}
                  className={cn(
                    "shrink-0 transition-transform duration-200 group-hover:scale-110 text-slate-400 dark:text-slate-500",
                    {
                      "text-white dark:text-white": isActive,
                    }
                  )}
                />
                {isOpen && (
                  <span className="text-xs font-bold tracking-wide">
                    {item.name}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Branding (Delhi Govt style) */}
      {isOpen && (
        <div className="p-4 border-t border-slate-200/50 dark:border-slate-800/50 text-center">
          <span className="text-[9px] uppercase font-extrabold tracking-widest text-slate-400">
            Delhi Smart City
          </span>
          <span className="block text-[8px] text-slate-500 mt-0.5">Gov-AI Enforcement Dept.</span>
        </div>
      )}
    </aside>
  );
}

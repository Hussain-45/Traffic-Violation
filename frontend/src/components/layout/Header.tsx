"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { useApp } from "../../lib/api";
import { Badge } from "../ui/Badge";

export function Header() {
  const pathname = usePathname();
  const { backendOnline, sidebarCollapsed, toggleSidebar } = useApp();

  const getPageTitle = (path: string): string => {
    switch (path) {
      case "/":
        return "Dashboard Overview";
      case "/live":
        return "Live Monitoring Feed";
      case "/violations":
        return "Violations Registry";
      case "/evidence":
        return "Evidence Locker";
      case "/reports":
        return "Analytics Reports";
      case "/analytics":
        return "Metrics & Charts";
      case "/settings":
        return "System Settings";
      default:
        return "Traffic Violation AI";
    }
  };

  return (
    <header className="h-16 border-b border-navy-accent/50 bg-navy-dark/40 backdrop-blur-md sticky top-0 z-20 flex items-center justify-between px-6">
      {/* Mobile Toggle & Page Title */}
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="p-1 hover:bg-navy-accent/50 rounded-lg text-slate-400 hover:text-brand-cyan transition-colors duration-200 cursor-pointer block md:hidden"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-6 h-6"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
            />
          </svg>
        </button>

        <div>
          <h2 className="text-base font-bold text-slate-100 tracking-tight leading-none md:block hidden">
            Traffic Violation AI
          </h2>
          <span className="text-xs font-semibold text-slate-400 mt-1 block">
            {getPageTitle(pathname)}
          </span>
        </div>
      </div>

      {/* Control Actions / User Meta */}
      <div className="flex items-center gap-4">
        {/* Backend Status indicator */}
        <div className="flex items-center gap-1.5 select-none">
          <span className="text-xs text-slate-400 font-medium">Backend:</span>
          {backendOnline ? (
            <Badge variant="success" className="gap-1 animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-status-green"></span>
              Online
            </Badge>
          ) : (
            <Badge variant="danger" className="gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-status-red"></span>
              Offline
            </Badge>
          )}
        </div>

        {/* Theme Toggle Placeholder */}
        <button className="p-2 hover:bg-navy-accent/40 rounded-lg border border-navy-accent/30 text-slate-400 hover:text-brand-cyan transition-all cursor-pointer">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-4 h-4"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z"
            />
          </svg>
        </button>

        {/* Notifications Placeholder */}
        <button className="p-2 hover:bg-navy-accent/40 rounded-lg border border-navy-accent/30 text-slate-400 hover:text-brand-cyan relative cursor-pointer">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="w-4 h-4"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0"
            />
          </svg>
          <span className="absolute top-1 right-1 w-2 h-2 bg-brand-cyan rounded-full"></span>
        </button>

        <div className="h-6 w-px bg-navy-accent/30"></div>

        {/* User Account Placeholder */}
        <div className="flex items-center gap-2 select-none">
          <div className="w-8 h-8 rounded-full bg-navy-accent border border-navy-accent/50 flex items-center justify-center font-semibold text-xs text-brand-cyan">
            JD
          </div>
          <span className="text-xs font-semibold text-slate-300 md:block hidden">
            John Doe
          </span>
        </div>
      </div>
    </header>
  );
}
export default Header;

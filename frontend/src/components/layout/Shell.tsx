"use client";

import React from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { useApp } from "../../lib/api";

export function Shell({ children }: { children: React.ReactNode }) {
  const { sidebarCollapsed } = useApp();

  return (
    <div className="min-h-screen bg-navy-darker flex text-slate-100 selection:bg-brand-cyan/20 selection:text-brand-cyan">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Layout Area */}
      <div
        className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${
          sidebarCollapsed ? "pl-16" : "pl-64"
        }`}
      >
        {/* Top Header */}
        <Header />

        {/* Dynamic Page Content */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          {children}
        </main>

        {/* Minimal Footer */}
        <Footer />
      </div>
    </div>
  );
}
export default Shell;

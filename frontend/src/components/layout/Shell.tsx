"use client";

import React from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { useApp } from "../../lib/api";
import { usePathname } from "next/navigation";
import { AuthGuard } from "../auth/AuthGuard";

export function Shell({ children }: { children: React.ReactNode }) {
  const { sidebarCollapsed } = useApp();
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  return (
    <div className="min-h-screen bg-navy-darker flex text-slate-100 selection:bg-brand-cyan/20 selection:text-brand-cyan">
      {/* Sidebar Navigation */}
      {!isLoginPage && <Sidebar />}

      {/* Main Layout Area */}
      <div
        className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${
          isLoginPage ? "pl-0" : sidebarCollapsed ? "pl-16" : "pl-64"
        }`}
      >
        {/* Top Header */}
        {!isLoginPage && <Header />}

        {/* Dynamic Page Content */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          {isLoginPage ? children : <AuthGuard>{children}</AuthGuard>}
        </main>

        {/* Minimal Footer */}
        {!isLoginPage && <Footer />}
      </div>
    </div>
  );
}
export default Shell;

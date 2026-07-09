"use client";

import React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/components/auth/AuthContext";

export default function UnauthorizedPage() {
  const { logout, user } = useAuth();

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="bg-navy-light border border-navy-accent/50 p-8 rounded-2xl w-full max-w-md shadow-2xl text-center">
        <div className="text-5xl mb-4 select-none">🚫</div>
        <h2 className="text-xl font-bold text-slate-100 mt-4">Privileged View Restricted</h2>
        <p className="text-xs text-slate-400 mt-2 max-w-xs mx-auto">
          Your active account role (<span className="text-brand-cyan font-mono font-semibold">{user?.role || "viewer"}</span>) does not possess sufficient clearance permissions to access this page.
        </p>

        <div className="mt-8 space-y-3">
          <Link href="/" className="block">
            <Button variant="primary" className="w-full">
              Back to Main Dashboard
            </Button>
          </Link>
          <Button variant="outline" className="w-full text-xs" onClick={logout}>
            Authenticate with Another Account
          </Button>
        </div>
      </div>
    </div>
  );
}

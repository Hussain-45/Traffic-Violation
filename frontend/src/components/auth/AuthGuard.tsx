"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "./AuthContext";

interface AuthGuardProps {
  children: React.ReactNode;
  requiredPermission?: string;
}

export function AuthGuard({ children, requiredPermission }: AuthGuardProps) {
  const { user, token, loading, hasPermission } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading) {
      if (!token) {
        // Redirection to Login
        router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
      } else if (requiredPermission && !hasPermission(requiredPermission)) {
        // Redirection to Unauthorized View
        router.push("/unauthorized");
      }
    }
  }, [token, loading, requiredPermission, pathname]);

  if (loading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-3">
        <div className="w-10 h-10 border-4 border-brand-cyan border-t-transparent rounded-full animate-spin" />
        <span className="text-slate-400 text-sm">Verifying authorization access...</span>
      </div>
    );
  }

  // Double-verify permission if required
  if (!token || (requiredPermission && !hasPermission(requiredPermission))) {
    return null; // prevents rendering layout before redirect triggers
  }

  return <>{children}</>;
}

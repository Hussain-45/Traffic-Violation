"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";
import { Button } from "@/components/ui/Button";

export default function LoginPage() {
  const { login, token } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/";

  // Redirect if already authenticated
  useEffect(() => {
    if (token) {
      router.push(redirect);
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      const success = await login(username, password, rememberMe);
      if (success) {
        router.push(redirect);
      } else {
        setErrorMsg("Incorrect username or password configuration.");
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to establish authorization context.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[75vh] flex items-center justify-center p-4">
      <div className="bg-navy-light/45 border border-navy-accent/50 p-8 rounded-2xl w-full max-w-md shadow-2xl backdrop-blur-md relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute -top-12 -left-12 w-28 h-28 rounded-full bg-brand-cyan/15 blur-xl pointer-events-none" />
        <div className="absolute -bottom-12 -right-12 w-28 h-28 rounded-full bg-brand-blue/15 blur-xl pointer-events-none" />

        <div className="text-center mb-7">
          <div className="w-12 h-12 bg-gradient-to-tr from-brand-blue to-brand-cyan rounded-xl flex items-center justify-center font-bold text-lg text-white mx-auto shadow-md shadow-brand-cyan/20">
            TV
          </div>
          <h2 className="text-xl font-bold text-slate-100 mt-4">Smart Traffic Monitor</h2>
          <p className="text-xs text-slate-400 mt-1">Provide security credentials to sign in.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {errorMsg && (
            <div className="bg-status-red/10 border border-status-red/30 text-status-red text-xs p-3.5 rounded-lg font-medium">
              ⚠️ {errorMsg}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              placeholder="Enter username"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              placeholder="••••••••"
              required
            />
          </div>

          <div className="flex items-center justify-between mt-6">
            <label className="relative flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 bg-navy-dark border-navy-accent rounded accent-brand-cyan"
              />
              <span className="text-xs font-medium text-slate-400">Remember session for 30 days</span>
            </label>
          </div>

          <Button variant="primary" type="submit" className="w-full" disabled={loading}>
            {loading ? "Authenticating user context..." : "Sign In"}
          </Button>
        </form>
      </div>
    </div>
  );
}

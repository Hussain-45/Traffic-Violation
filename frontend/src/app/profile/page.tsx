"use client";

import React, { useState } from "react";
import { useAuth } from "@/components/auth/AuthContext";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { Button } from "@/components/ui/Button";

export default function ProfilePage() {
  const { user, changePassword } = useAuth();
  const [oldPass, setOldPass] = useState("");
  const [newPass, setNewPass] = useState("");
  const [confirmPass, setConfirmPass] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (newPass !== confirmPass) {
      setErrorMsg("New passwords do not match.");
      return;
    }
    if (newPass.length < 6) {
      setErrorMsg("Password must be at least 6 characters long.");
      return;
    }

    setSaving(true);
    try {
      const success = await changePassword(oldPass, newPass);
      if (success) {
        setSuccessMsg("Password changed successfully. Other active sessions revoked.");
        setOldPass("");
        setNewPass("");
        setConfirmPass("");
      } else {
        setErrorMsg("Incorrect current password credentials.");
      }
    } catch {
      setErrorMsg("Failed to update password settings.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AuthGuard>
      <div className="space-y-8 animate-fadeIn max-w-4xl mx-auto">
        <div className="border-b border-navy-accent/30 pb-5">
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <span>👤</span> User Profile Settings
          </h1>
          <p className="text-xs text-slate-400 mt-1">Manage credentials, view authorization scopes, and user session details.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* User profile details info card */}
          <div className="md:col-span-1 bg-navy-light rounded-xl border border-navy-accent/40 p-6 space-y-5">
            <div className="text-center pb-4 border-b border-navy-accent/35">
              <div className="w-16 h-16 rounded-full bg-brand-blue/10 border border-brand-cyan/25 flex items-center justify-center font-bold text-2xl text-brand-cyan mx-auto shadow-inner">
                {user?.full_name.charAt(0) || "U"}
              </div>
              <h3 className="font-bold text-slate-100 mt-3 text-base">{user?.full_name}</h3>
              <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-brand-cyan bg-brand-cyan/10 px-2 py-0.5 rounded border border-brand-cyan/15 inline-block mt-1">
                {user?.role}
              </span>
            </div>

            <div className="space-y-3.5 text-xs text-slate-300">
              <div>
                <span className="block text-slate-500 uppercase tracking-wider font-semibold mb-0.5">Username</span>
                <span className="font-mono text-slate-200">{user?.username}</span>
              </div>
              <div>
                <span className="block text-slate-500 uppercase tracking-wider font-semibold mb-0.5">Email</span>
                <span className="text-slate-200">{user?.email}</span>
              </div>
              <div>
                <span className="block text-slate-500 uppercase tracking-wider font-semibold mb-0.5">Account Status</span>
                <span className="flex items-center gap-1.5 mt-0.5">
                  <span className="w-2 h-2 rounded-full bg-status-green" />
                  <span className="capitalize">{user?.status}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Configuration Forms */}
          <div className="md:col-span-2 space-y-6">
            {/* Scopes details card */}
            <div className="bg-navy-light rounded-xl border border-navy-accent/40 p-6">
              <h3 className="font-bold text-slate-100 text-sm mb-3 flex items-center gap-2">
                <span>🔑</span> Authorized Permission Scopes
              </h3>
              <div className="flex flex-wrap gap-2 mt-4">
                {user?.permissions.map((perm) => (
                  <span
                    key={perm}
                    className="px-2.5 py-1 bg-navy-accent/50 text-[10px] text-slate-300 font-mono rounded border border-navy-accent/60"
                  >
                    {perm}
                  </span>
                ))}
              </div>
            </div>

            {/* Change Password form card */}
            <div className="bg-navy-light rounded-xl border border-navy-accent/40 p-6">
              <h3 className="font-bold text-slate-100 text-sm mb-4 flex items-center gap-2">
                <span>🔒</span> Update Security Password
              </h3>

              <form onSubmit={handleSubmit} className="space-y-4">
                {errorMsg && (
                  <div className="bg-status-red/10 border border-status-red/30 text-status-red text-xs p-3.5 rounded-lg font-medium">
                    ⚠️ {errorMsg}
                  </div>
                )}
                {successMsg && (
                  <div className="bg-status-green/10 border border-status-green/30 text-status-green text-xs p-3.5 rounded-lg font-medium">
                    ✅ {successMsg}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Current Password</label>
                  <input
                    type="password"
                    value={oldPass}
                    onChange={(e) => setOldPass(e.target.value)}
                    className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
                    placeholder="••••••••"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">New Password</label>
                  <input
                    type="password"
                    value={newPass}
                    onChange={(e) => setNewPass(e.target.value)}
                    className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
                    placeholder="••••••••"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Confirm New Password</label>
                  <input
                    type="password"
                    value={confirmPass}
                    onChange={(e) => setConfirmPass(e.target.value)}
                    className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
                    placeholder="••••••••"
                    required
                  />
                </div>

                <div className="flex justify-end pt-2">
                  <Button variant="primary" type="submit" disabled={saving}>
                    {saving ? "Saving changes..." : "Save Password"}
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}

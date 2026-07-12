"use client";

import React, { useState, useEffect } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/components/auth/AuthContext";
import { useApp } from "@/lib/api";
import { BACKEND_URL } from "@/lib/apiClient";

export default function SettingsPage() {
  const { token, user } = useAuth();
  const { backendOnline } = useApp();

  const [activeTab, setActiveTab] = useState("thresholds");
  const [loading, setLoading] = useState(true);

  // 1. Threshold Settings State
  const [aiMode, setAiMode] = useState("simulated");
  const [confidence, setConfidence] = useState(0.5);
  const [speedLimit, setSpeedLimit] = useState(60.0);

  // 2. Fines Settings State
  const [fines, setFines] = useState<any[]>([]);

  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const triggerToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchSettings = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      // 1. Fetch Thresholds
      const threshRes = await fetch(`${BACKEND_URL}/api/v1/settings/thresholds`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (threshRes.ok) {
        const tData = await threshRes.json();
        setAiMode(tData.ai_mode || "simulated");
        setConfidence(tData.confidence_threshold ?? 0.5);
        setSpeedLimit(tData.speed_limit ?? 60.0);
      }

      // 2. Fetch Fines
      const finesRes = await fetch(`${BACKEND_URL}/api/v1/settings/fines`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (finesRes.ok) {
        const fData = await finesRes.json();
        setFines(fData || []);
      }
    } catch {
      triggerToast("Error retrieving configuration parameters.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchSettings();
    }
  }, [token, backendOnline]);

  const handleSaveThresholds = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/settings/thresholds`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ai_mode: aiMode,
          confidence_threshold: parseFloat(String(confidence)),
          speed_limit: parseFloat(String(speedLimit)),
        }),
      });
      if (res.ok) {
        triggerToast("AI Thresholds updated. System sync in progress.");
        fetchSettings();
      } else {
        triggerToast("Failed to save AI settings.", "error");
      }
    } catch {
      triggerToast("Connection error updating settings.", "error");
    }
  };

  const handleUpdateFine = async (type: string, amount: number) => {
    if (!token) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/settings/fines/${type}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ amount: parseFloat(String(amount)) }),
      });
      if (res.ok) {
        triggerToast(`Fine rule for ${type.replace(/_/g, " ").toUpperCase()} updated.`);
        fetchSettings();
      } else {
        triggerToast("Failed to update fine amount.", "error");
      }
    } catch {
      triggerToast("Connection error updating fine rule.", "error");
    }
  };

  if (user?.role !== "admin" && user?.role !== "officer") {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center text-center p-6">
        <div className="text-4xl mb-4">🚫</div>
        <h2 className="text-lg font-bold text-slate-200">Clearance Required</h2>
        <p className="text-xs text-slate-400 mt-1 max-w-xs">
          Only administrator accounts are authorized to modify AI thresholds and violation fine amounts.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-xl text-white text-xs font-semibold flex items-center gap-2 ${
          toast.type === "success" ? "bg-emerald-600" : "bg-rose-600"
        }`}>
          <span>{toast.type === "success" ? "✓" : "⚠️"}</span>
          <span>{toast.message}</span>
        </div>
      )}

      <PageHeader
        title="System Settings"
        description="Configure YOLO camera streams, OCR threshold sensitivity, fine pricing templates, and email alert relays."
      />

      {/* Tabs */}
      <div className="flex border-b border-navy-accent/40 gap-6">
        {[
          { id: "thresholds", label: "AI Thresholds", icon: "🧠" },
          { id: "fines", label: "Fine Challan Pricing", icon: "💸" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`pb-3.5 text-sm font-medium transition-all duration-200 border-b-2 flex items-center gap-2 cursor-pointer ${
              activeTab === tab.id
                ? "border-brand-cyan text-brand-cyan"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="py-12 flex flex-col items-center justify-center gap-3">
          <div className="w-10 h-10 border-4 border-brand-cyan border-t-transparent rounded-full animate-spin" />
          <span className="text-slate-400 text-xs">Querying dynamic settings...</span>
        </div>
      ) : (
        <div>
          {/* Thresholds Panel */}
          {activeTab === "thresholds" && (
            <Card className="max-w-2xl">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle>AI Inference Parameters</CardTitle>
                <Badge variant="warning">Restart Required</Badge>
              </CardHeader>
              <CardContent className="pt-4">
                <form onSubmit={handleSaveThresholds} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Execution Mode</label>
                    <select
                      value={aiMode}
                      onChange={(e) => setAiMode(e.target.value)}
                      className="w-full bg-navy-dark border border-navy-accent/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-cyan"
                    >
                      <option value="active">Active (Full YOLO Inference)</option>
                      <option value="simulated">Simulated / Mock Detections</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Confidence Cut-off (Value: {confidence})
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="0.95"
                      step="0.05"
                      value={confidence}
                      onChange={(e) => setConfidence(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-navy-dark rounded-lg appearance-none cursor-pointer accent-brand-cyan"
                    />
                    <span className="text-[10px] text-slate-500 block">
                      Minimum probability box scores for seatbelt, helmet, and phone detections.
                    </span>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Urban Speed Limit (km/h)
                    </label>
                    <input
                      type="number"
                      value={speedLimit}
                      onChange={(e) => setSpeedLimit(parseFloat(e.target.value))}
                      className="w-full bg-navy-dark border border-navy-accent/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none"
                      required
                    />
                    <span className="text-[10px] text-slate-500 block">
                      Dispatches overspeed violation challenges for tracks exceeding this rate.
                    </span>
                  </div>

                  <Button variant="primary" type="submit" className="w-full mt-4">
                    💾 Save AI Configs
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Fine Rules Panel */}
          {activeTab === "fines" && (
            <Card className="max-w-3xl">
              <CardHeader>
                <CardTitle>Challan Fine Rates Template</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-navy-accent/20">
                  {fines.map((item) => (
                    <div key={item.violation_type} className="px-6 py-4 flex items-center justify-between hover:bg-navy-light/10 transition-colors">
                      <div className="space-y-1 pr-4">
                        <span className="text-sm font-bold text-slate-200 capitalize">
                          {item.violation_type.replace(/_/g, " ")}
                        </span>
                        <p className="text-[11px] text-slate-400 leading-tight">
                          {item.description || "Automatic fine rule assessment template."}
                        </p>
                      </div>
                      <div className="flex items-center gap-3.5">
                        <span className="text-slate-400 text-xs">₹</span>
                        <input
                          type="number"
                          defaultValue={item.amount}
                          onBlur={(e) => {
                            const val = parseFloat(e.target.value);
                            if (val !== item.amount) {
                              handleUpdateFine(item.violation_type, val);
                            }
                          }}
                          className="w-24 bg-navy-dark border border-navy-accent/40 rounded px-2 py-1 text-xs text-slate-200 font-mono text-right focus:outline-none"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

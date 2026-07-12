"use client";

import { useAuth } from "@/components/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { useApp } from "@/lib/api";
import { BACKEND_URL } from "@/lib/apiClient";
import React, { useEffect, useState } from "react";

export default function ReportsPage() {
  const { token } = useAuth();
  const { backendOnline } = useApp();

  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Form Fields
  const [title, setTitle] = useState("");
  const [reportType, setReportType] = useState("violations");
  const [startDate, setStartDate] = useState(new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString().split("T")[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split("T")[0]);
  const [fileFormat, setFileFormat] = useState("csv");

  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const triggerToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchReports = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/reports`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        const data = await res.json();
        setReports(data || []);
      } else {
        triggerToast("Failed to retrieve generated reports history.", "error");
      }
    } catch {
      triggerToast("Error connecting to reporting services.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchReports();
    }
  }, [token, backendOnline]);

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !backendOnline) return;

    setGenerating(true);
    try {
      const payload = {
        title: title || `${reportType.toUpperCase()} Audit Report`,
        report_type: reportType,
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        file_format: fileFormat,
      };

      const res = await fetch(`${BACKEND_URL}/api/v1/reports`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        triggerToast("Report generated in background successfully.");
        setTitle("");
        fetchReports();
      } else {
        triggerToast("Failed to compile report metrics.", "error");
      }
    } catch {
      triggerToast("Connection error generating report.", "error");
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteReport = async (id: number) => {
    if (!token) return;
    if (!window.confirm("Are you sure you want to delete this report log from historical files?")) return;

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/reports/${id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        triggerToast("Report log and associated files deleted.");
        fetchReports();
      } else {
        triggerToast("Failed to delete report log.", "error");
      }
    } catch {
      triggerToast("Error contacting reporting server.", "error");
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-xl text-white text-xs font-semibold flex items-center gap-2 ${toast.type === "success" ? "bg-emerald-600" : "bg-rose-600"
          }`}>
          <span>{toast.type === "success" ? "✓" : "⚠️"}</span>
          <span>{toast.message}</span>
        </div>
      )}

      <PageHeader
        title="Analytics Reports"
        description="Generate, customize, and export PDF traffic safety audit sheets, violation stats, and citation logs."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generator Form */}
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Generate Custom Report</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleGenerateReport} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Report Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Q2 Traffic Safety Summary"
                  className="w-full bg-navy-dark border border-navy-accent/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-cyan"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Report Type</label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full bg-navy-dark border border-navy-accent/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-cyan"
                >
                  <option value="violations">Violations Audit Log</option>
                  <option value="revenue">Fine & Revenue Summary</option>
                  <option value="analytics">AI Detector Accuracy Stats</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full bg-navy-dark border border-navy-accent/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-cyan"
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full bg-navy-dark border border-navy-accent/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-cyan"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Export Format</label>
                <div className="grid grid-cols-3 gap-2">
                  {["csv", "xlsx", "pdf"].map((format) => (
                    <button
                      key={format}
                      type="button"
                      onClick={() => setFileFormat(format)}
                      className={`py-2 text-xs font-semibold uppercase rounded-lg border transition-colors ${fileFormat === format
                          ? "bg-brand-cyan border-brand-cyan text-navy-darker"
                          : "border-navy-accent/50 text-slate-400 hover:text-slate-200"
                        }`}
                    >
                      {format}
                    </button>
                  ))}
                </div>
              </div>

              <Button variant="primary" type="submit" className="w-full mt-4" disabled={generating || !backendOnline}>
                {generating ? "Compiling tabular metrics..." : "Generate & Save Report"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* History Table */}
        <div className="lg:col-span-2">
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle>Report History Locker</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col pt-0">
              {loading ? (
                <div className="py-12 flex flex-col items-center justify-center gap-3 flex-1">
                  <div className="w-10 h-10 border-4 border-brand-cyan border-t-transparent rounded-full animate-spin" />
                  <span className="text-slate-400 text-xs">Querying historical logs...</span>
                </div>
              ) : reports.length > 0 ? (
                <div className="border border-navy-accent/40 rounded-xl overflow-hidden shadow-xl flex-1">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-navy-dark/70 border-b border-navy-accent/40 text-slate-400 uppercase tracking-wider text-[10px] font-semibold">
                          <th className="p-4">Report Details</th>
                          <th className="p-4">Range</th>
                          <th className="p-4">Created At</th>
                          <th className="p-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-navy-accent/20">
                        {reports.map((item) => (
                          <tr key={item.id} className="hover:bg-navy-light/10 text-slate-300">
                            <td className="p-4">
                              <div className="font-semibold text-slate-100">{item.title}</div>
                              <div className="text-[10px] text-slate-500 uppercase mt-0.5 font-mono">
                                Type: {item.report_type} • ID: #{item.id}
                              </div>
                            </td>
                            <td className="p-4 font-mono text-[10px] text-slate-400">
                              {new Date(item.start_date).toLocaleDateString()} - {new Date(item.end_date).toLocaleDateString()}
                            </td>
                            <td className="p-4 font-mono text-[10px] text-slate-400">
                              {new Date(item.created_at).toLocaleString()}
                            </td>
                            <td className="p-4 text-right">
                              <div className="flex items-center justify-end gap-3.5">
                                <a
                                  href={`${BACKEND_URL}${item.file_path}`}
                                  download
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs font-semibold text-brand-cyan hover:underline"
                                >
                                  📥 Download
                                </a>
                                <button
                                  onClick={() => handleDeleteReport(item.id)}
                                  className="text-xs font-semibold text-status-red hover:underline"
                                >
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <EmptyState
                  title="No Reports Generated"
                  description="Choose parameters in the compiler console to create safety summaries."
                  icon={<span>📄</span>}
                  action={<Button variant="outline" size="sm" onClick={fetchReports}>Refresh Log</Button>}
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

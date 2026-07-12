"use client";

import { useAuth } from "@/components/auth/AuthContext";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { useApp } from "@/lib/api";
import { BACKEND_URL } from "@/lib/apiClient";
import React, { useEffect, useState } from "react";

export default function ViolationsPage() {
  const { token } = useAuth();
  const { backendOnline } = useApp();

  // Filters & State
  const [violations, setViolations] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchPlate, setSearchPlate] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterCamera, setFilterCamera] = useState("");
  const [page, setPage] = useState(1);
  const limit = 10;

  // Selected for Bulk Actions
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const triggerToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchViolations = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const skip = (page - 1) * limit;
      let url = `${BACKEND_URL}/api/v1/violations?skip=${skip}&limit=${limit}`;
      if (searchPlate) url += `&plate=${encodeURIComponent(searchPlate)}`;
      if (filterType) url += `&type=${encodeURIComponent(filterType)}`;
      if (filterStatus) url += `&status=${encodeURIComponent(filterStatus)}`;
      if (filterCamera) url += `&camera_id=${encodeURIComponent(filterCamera)}`;

      const res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      if (res.ok) {
        const data = await res.json();
        setViolations(data.items || []);
        setTotal(data.total || 0);
      } else {
        triggerToast("Failed to fetch violations log.", "error");
      }
    } catch {
      triggerToast("Error connecting to backend database.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchViolations();
    }
  }, [token, page, filterType, filterStatus, filterCamera, backendOnline]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchViolations();
  };

  const handleUpdateStatus = async (id: number, newStatus: string) => {
    if (!token) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/violations/${id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        triggerToast(`Violation status updated to ${newStatus}.`);
        fetchViolations();
      } else {
        triggerToast("Failed to update status.", "error");
      }
    } catch {
      triggerToast("Error updating status.", "error");
    }
  };

  const handleBulkMarkReviewed = async () => {
    if (selectedIds.length === 0) return;
    let successCount = 0;
    for (const id of selectedIds) {
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/violations/${id}`, {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ status: "resolved" }),
        });
        if (res.ok) successCount++;
      } catch { }
    }
    triggerToast(`Bulk Action: Marked ${successCount} violations as Resolved.`);
    setSelectedIds([]);
    fetchViolations();
  };

  const handleExport = () => {
    if (violations.length === 0) return;
    const headers = ["Timestamp", "Plate", "Vehicle Type", "Camera ID", "Violation Type", "Confidence", "Status", "Fine"];
    const rows = violations.map((v) => [
      new Date(v.timestamp).toLocaleString(),
      v.vehicle.license_plate,
      v.vehicle.type,
      v.camera_id,
      v.type,
      v.confidence_score,
      v.status,
      v.fine_amount,
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `violations_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    triggerToast("CSV export compiled and downloaded.");
  };

  const handleToggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
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
        title="Violations Registry"
        description="Browse, filter, and review detected traffic violation events, license plate metadata, and fine status."
      >
        <Button variant="outline" size="sm" onClick={handleExport} disabled={violations.length === 0}>
          📥 Export List
        </Button>
      </PageHeader>

      {/* Filters Card */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-2">Plate Number</label>
              <input
                type="text"
                value={searchPlate}
                onChange={(e) => setSearchPlate(e.target.value)}
                placeholder="Search plate..."
                className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-xs rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              />
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-2">Violation Type</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-xs rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              >
                <option value="">All Types</option>
                <option value="red_light_jump">Red Light Jump</option>
                <option value="no_helmet">No Helmet</option>
                <option value="speed_violation">Speed Violation</option>
                <option value="wrong_side">Wrong Side Driving</option>
                <option value="triple_riding">Triple Riding</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-2">Fine Status</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-xs rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="paid">Paid</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>

            <div>
              <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-2">Camera ID</label>
              <input
                type="text"
                value={filterCamera}
                onChange={(e) => setFilterCamera(e.target.value)}
                placeholder="e.g. CAM-001"
                className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-xs rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              />
            </div>

            <div className="flex items-end">
              <Button variant="primary" type="submit" className="w-full py-2.5">
                🔍 Filter Results
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Selected Action Bar */}
      {selectedIds.length > 0 && (
        <div className="bg-navy-light/65 border border-brand-cyan/35 px-4 py-3 rounded-lg flex items-center justify-between">
          <span className="text-xs text-slate-300">
            Selected <strong className="text-brand-cyan font-mono">{selectedIds.length}</strong> items for bulk actions.
          </span>
          <div className="flex gap-2">
            <Button variant="primary" size="sm" onClick={handleBulkMarkReviewed}>
              ✓ Mark Reviewed
            </Button>
            <Button variant="outline" size="sm" onClick={() => setSelectedIds([])}>
              Clear
            </Button>
          </div>
        </div>
      )}

      {/* Main Table */}
      {loading ? (
        <div className="py-12 flex flex-col items-center justify-center gap-3">
          <div className="w-10 h-10 border-4 border-brand-cyan border-t-transparent rounded-full animate-spin" />
          <span className="text-slate-400 text-xs">Querying database...</span>
        </div>
      ) : violations.length > 0 ? (
        <div className="bg-navy-light/20 border border-navy-accent/40 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-navy-dark/70 border-b border-navy-accent/40 text-slate-400 uppercase tracking-wider text-[10px] font-semibold">
                  <th className="p-4 w-10">
                    <input
                      type="checkbox"
                      checked={selectedIds.length === violations.length}
                      onChange={() => {
                        if (selectedIds.length === violations.length) setSelectedIds([]);
                        else setSelectedIds(violations.map(v => v.id));
                      }}
                      className="rounded accent-brand-cyan"
                    />
                  </th>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">Plate</th>
                  <th className="p-4">Vehicle</th>
                  <th className="p-4">Camera</th>
                  <th className="p-4">Violation</th>
                  <th className="p-4 text-center">Confidence</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Fine</th>
                  <th className="p-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-accent/20">
                {violations.map((v) => (
                  <tr key={v.id} className="hover:bg-navy-light/10 text-slate-300">
                    <td className="p-4">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(v.id)}
                        onChange={() => handleToggleSelect(v.id)}
                        className="rounded accent-brand-cyan"
                      />
                    </td>
                    <td className="p-4 font-mono text-[10px]">
                      {new Date(v.timestamp).toLocaleString()}
                    </td>
                    <td className="p-4 font-mono font-bold text-slate-100">
                      {v.vehicle.license_plate}
                    </td>
                    <td className="p-4 capitalize">
                      {v.vehicle.color} {v.vehicle.brand} ({v.vehicle.type})
                    </td>
                    <td className="p-4 font-mono">{v.camera_id}</td>
                    <td className="p-4 font-semibold capitalize text-brand-cyan">
                      {v.type.replace(/_/g, " ")}
                    </td>
                    <td className="p-4 text-center font-mono font-bold text-brand-orange">
                      {Math.round(v.confidence_score * 100)}%
                    </td>
                    <td className="p-4">
                      <Badge variant={v.status === "paid" ? "success" : v.status === "pending" ? "danger" : "info"}>
                        {v.status.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="p-4 text-right font-mono font-bold text-slate-100">
                      ₹{v.fine_amount.toLocaleString()}
                    </td>
                    <td className="p-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {v.evidence_image_path && (
                          <a
                            href={`${BACKEND_URL}/${v.evidence_image_path}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1 hover:bg-navy-accent/50 rounded text-slate-400 hover:text-brand-cyan transition-colors"
                            title="View Evidence Image"
                          >
                            🖼️
                          </a>
                        )}
                        {v.status === "pending" && (
                          <button
                            onClick={() => handleUpdateStatus(v.id, "resolved")}
                            className="text-[10px] font-semibold text-emerald-400 hover:underline"
                          >
                            Mark Reviewed
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="px-5 py-4 bg-navy-dark/30 border-t border-navy-accent/30 flex items-center justify-between">
            <span className="text-[10px] text-slate-400 uppercase tracking-wide">
              Showing page <strong className="text-brand-cyan font-mono">{page}</strong> of{" "}
              <strong className="text-slate-200 font-mono">{Math.ceil(total / limit) || 1}</strong> ({total} entries)
            </span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                Previous
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page * limit >= total}>
                Next
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <EmptyState
          title="No Violations Yet"
          description="Try triggering camera connections or uploading custom video evidence files to pop records."
          icon={<span>🚨</span>}
          action={<Button variant="outline" size="sm" onClick={fetchViolations}>Refresh Feed</Button>}
        />
      )}
    </div>
  );
}

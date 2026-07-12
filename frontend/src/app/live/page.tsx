"use client";

import React, { useState, useEffect, useRef } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useApp } from "@/lib/api";
import { BACKEND_URL } from "@/lib/apiClient";

// ── Types ───────────────────────────────────────────────────────────────────

interface Detections {
  total_vehicles: number;
  car: number;
  motorcycle: number;
  truck: number;
  bus: number;
  person: number;
  bicycle: number;
}

interface TrackingStats {
  active_tracks: number;
  unique_ids_seen: number;
  lost_tracks: number;
  tracking_fps: number;
}

interface HelmetStats {
  helmet_count: number;
  no_helmet_count: number;
  detection_status: string;
  model_status: string;
  training_status: string;
}

interface SeatBeltStats {
  seat_belt_count: number;
  no_seat_belt_count: number;
  unknown_count: number;
  detection_status: string;
  model_status: string;
  training_status: string;
}

interface MobilePhoneStats {
  phone_count: number;
  no_phone_count: number;
  unknown_count: number;
  detection_status: string;
  model_status: string;
  training_status: string;
}

interface TrafficSignalStats {
  red_count: number;
  yellow_count: number;
  green_count: number;
  unknown_count: number;
  detection_status: string;
  model_status: string;
  training_status: string;
}

interface WrongSideStats {
  wrong_side_count: number;
  correct_direction_count: number;
  unknown_count: number;
  detection_status: string;
  model_status: string;
  training_status: string;
}

interface TripleRidingStats {
  single_rider_count: number;
  double_riding_count: number;
  triple_riding_count: number;
  unknown_count: number;
  detection_status: string;
  model_status: string;
  association_status: string;
}

interface NumberPlateStats {
  detecting_count: number;
  stable_count: number;
  unknown_count: number;
  crop_ready_count: number;
  detection_status: string;
  model_status: string;
  training_status: string;
}

interface OCRStats {
  requests_count: number;
  verified_count: number;
  rejected_count: number;
  avg_confidence: number;
  detection_status: string;
  model_status: string;
  engine_name: string;
}

interface CameraStatus {
  connected: boolean;
  fps: number;
  width: number;
  height: number;
  source_type: string;
  source: string | number;
  dropped_frames: number;
  reconnect_attempts: number;
  detections: Detections;
  tracking: TrackingStats;
  helmet_stats?: HelmetStats;
  seat_belt_stats?: SeatBeltStats;
  mobile_phone_stats?: MobilePhoneStats;
  traffic_signal_stats?: TrafficSignalStats;
  wrong_side_stats?: WrongSideStats;
  triple_riding_stats?: TripleRidingStats;
  number_plate_stats?: NumberPlateStats;
  ocr_stats?: OCRStats;
}

// ── Constants ────────────────────────────────────────────────────────────────

const VEHICLE_CLASSES = [
  { key: "total_vehicles", label: "Vehicles",     icon: "🚗", color: "#06b6d4" },
  { key: "car",            label: "Cars",          icon: "🚘", color: "#10b981" },
  { key: "motorcycle",     label: "Motorcycles",   icon: "🏍️", color: "#f59e0b" },
  { key: "truck",          label: "Trucks",        icon: "🚛", color: "#ec4899" },
  { key: "bus",            label: "Buses",         icon: "🚌", color: "#8b5cf6" },
  { key: "bicycle",        label: "Bicycles",      icon: "🚲", color: "#3b82f6" },
  { key: "person",         label: "Persons",       icon: "🚶", color: "#64748b" },
] as const;

const ERROR_DETAILS: Record<string, { title: string; desc: string; icon: string }> = {
  "Camera Not Found": {
    title: "Camera Device Not Found",
    desc: "Could not open the selected device. Ensure it is connected and not in use by another application.",
    icon: "⚠️",
  },
  "Connection Lost": {
    title: "Feed Connection Lost",
    desc: "Unable to reach the backend stream. Attempting to reconnect automatically…",
    icon: "📡",
  },
  "Invalid URL": {
    title: "Invalid Feed Source URL",
    desc: "The RTSP or IP camera URL is invalid or refused connection. Check syntax and credentials.",
    icon: "🌐",
  },
  "Video Ended": {
    title: "Video Stream Stopped",
    desc: "The feed was manually disconnected or the video file has reached its end.",
    icon: "⏹️",
  },
  "Permission Denied": {
    title: "Hardware Access Denied",
    desc: "The OS refused access to the selected camera. Check application permissions.",
    icon: "🔒",
  },
};

// ── Component ─────────────────────────────────────────────────────────────────

export default function LiveMonitoringPage() {
  const { backendOnline } = useApp();
  const [status, setStatus] = useState<CameraStatus | null>(null);
  const [sourceType, setSourceType] = useState("Webcam");
  const [sourceInput, setSourceInput] = useState("0");
  const [connecting, setConnecting] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [customError, setCustomError] = useState<string | null>(null);
  const [streamKey, setStreamKey] = useState(Date.now());

  const videoRef = useRef<HTMLDivElement>(null);

  // ── Polling ────────────────────────────────────────────────────────────────
  const fetchStatus = async () => {
    if (!backendOnline) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/camera/status`);
      if (res.ok) {
        const data: CameraStatus = await res.json();
        setStatus(data);
        setCustomError(data.connected ? null : "Connection Lost");
      }
    } catch {
      setCustomError("Connection Lost");
    }
  };

  useEffect(() => {
    fetchStatus();
    const id = setInterval(fetchStatus, 2000);
    return () => clearInterval(id);
  }, [backendOnline]);

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!backendOnline) return;
    setConnecting(true);
    setCustomError(null);

    const source: string | number =
      sourceType === "Webcam" && /^\d+$/.test(sourceInput)
        ? parseInt(sourceInput)
        : sourceInput;

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/camera/connect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source }),
      });
      if (!res.ok) {
        const data = await res.json();
        const msg: string = data.detail ?? "";
        setCustomError(
          msg.includes("open camera") ? "Camera Not Found"
          : msg.includes("permission") ? "Permission Denied"
          : "Invalid URL"
        );
      } else {
        setStreamKey(Date.now());
        await fetchStatus();
      }
    } catch {
      setCustomError("Connection Lost");
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!backendOnline) return;
    try {
      await fetch(`${BACKEND_URL}/api/v1/camera/disconnect`, { method: "POST" });
      await fetchStatus();
      setCustomError("Video Ended");
    } catch {
      setCustomError("Connection Lost");
    }
  };

  const toggleFullscreen = () => {
    if (!videoRef.current) return;
    if (!document.fullscreenElement) {
      videoRef.current.requestFullscreen().then(() => setFullscreen(true));
    } else {
      document.exitFullscreen().then(() => setFullscreen(false));
    }
  };

  useEffect(() => {
    const h = () => setFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", h);
    return () => document.removeEventListener("fullscreenchange", h);
  }, []);

  // ── Derived values ─────────────────────────────────────────────────────────
  const det = status?.detections;
  const trk = status?.tracking;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div>
      <PageHeader
        title="Live Monitoring Feed"
        description="Real-time vehicle detection + ByteTrack multi-object tracking powered by YOLOv8n."
      />

      {/* ── Detection Counter Strip ──────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
        {VEHICLE_CLASSES.map(({ key, label, icon, color }) => (
          <div
            key={key}
            className="rounded-xl border border-navy-accent/40 bg-navy-dark/60 p-3 flex flex-col items-center gap-1.5 transition-all hover:border-navy-accent"
            style={{ borderTopColor: color, borderTopWidth: "2px" }}
          >
            <span className="text-xl">{icon}</span>
            <span
              className="text-[22px] font-bold font-mono leading-none"
              style={{ color }}
            >
              {det ? (det as unknown as Record<string, number>)[key] ?? 0 : 0}
            </span>
            <span className="text-[10px] text-slate-400 text-center leading-tight">{label}</span>
          </div>
        ))}
      </div>

      {/* ── Tracking Statistics Strip ────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {[
          {
            label: "Active Tracks",
            value: trk?.active_tracks ?? 0,
            icon: "📍",
            color: "#06b6d4",
            desc: "Objects tracked this frame",
          },
          {
            label: "Unique IDs",
            value: trk?.unique_ids_seen ?? 0,
            icon: "🆔",
            color: "#10b981",
            desc: "Total IDs assigned since start",
          },
          {
            label: "Lost Tracks",
            value: trk?.lost_tracks ?? 0,
            icon: "👻",
            color: "#f59e0b",
            desc: "IDs not seen this frame",
          },
          {
            label: "Tracking FPS",
            value: trk ? `${trk.tracking_fps}` : "0",
            icon: "⚡",
            color: "#8b5cf6",
            desc: "ByteTrack update iterations/sec",
          },
        ].map(({ label, value, icon, color, desc }) => (
          <div
            key={label}
            className="rounded-xl border border-navy-accent/40 bg-navy-dark/60 px-4 py-3 flex items-center gap-4 hover:border-navy-accent transition-all"
            style={{ borderLeftColor: color, borderLeftWidth: "3px" }}
          >
            <span className="text-2xl">{icon}</span>
            <div>
              <div
                className="text-2xl font-bold font-mono leading-none"
                style={{ color }}
              >
                {value}
              </div>
              <div className="text-[11px] text-slate-300 font-medium mt-0.5">{label}</div>
              <div className="text-[10px] text-slate-500 mt-0.5">{desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Main Grid ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

        {/* Video Feed ─────────────────────────────────────────────────────── */}
        <div className="lg:col-span-3 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Live Camera Feed</CardTitle>
                <p className="text-xs text-slate-400 mt-1">
                  {status?.connected
                    ? `Source: ${status.source} (${status.source_type}) · YOLOv8n + ByteTrack`
                    : "No camera connected"}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={trk && trk.active_tracks > 0 ? "info" : "default"}>
                  {trk?.active_tracks ?? 0} tracked
                </Badge>
                <Badge variant={status?.connected ? "success" : "danger"}>
                  {status?.connected ? "LIVE" : "OFFLINE"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {/* Stream viewer */}
              <div
                ref={videoRef}
                className="aspect-video w-full rounded-lg bg-navy-dark border border-navy-accent/50 relative overflow-hidden"
              >
                {backendOnline ? (
                  status?.connected ? (
                    <img
                      key={streamKey}
                      src={`${BACKEND_URL}/api/v1/camera/stream`}
                      alt="Live annotated camera feed with ByteTrack IDs"
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center w-full h-full p-6 text-center animate-fadeIn">
                      <div className="w-14 h-14 bg-navy-accent/40 rounded-full flex items-center justify-center text-slate-500 mb-3 animate-pulse">
                        📹
                      </div>
                      <span className="text-sm font-bold text-slate-200">No Camera Connected</span>
                      <span className="text-xs text-slate-500 mt-1 max-w-xs">
                        Configure a camera index or network source URL in the stream control panel.
                      </span>
                    </div>
                  )
                ) : (
                  <div className="flex flex-col items-center justify-center w-full h-full p-6 text-center animate-fadeIn">
                    {/* Skeleton loader wrapper */}
                    <div className="w-full max-w-sm space-y-3">
                      <div className="h-4 bg-slate-700/20 rounded animate-pulse w-3/4 mx-auto" />
                      <div className="h-3 bg-slate-700/25 rounded animate-pulse w-1/2 mx-auto" />
                    </div>
                    <span className="text-xs font-semibold text-slate-500 mt-4">
                      Waiting for Camera...
                    </span>
                  </div>
                )}

                {/* Error overlay */}
                {customError && (
                  <div className="absolute inset-0 z-20 bg-navy-darker/90 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center">
                    <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center text-xl mb-4 animate-pulse">
                      {ERROR_DETAILS[customError]?.icon ?? "❓"}
                    </div>
                    <h4 className="text-sm font-bold text-slate-200">
                      {ERROR_DETAILS[customError]?.title ?? "Stream Error"}
                    </h4>
                    <p className="text-xs text-slate-400 max-w-sm mt-2 leading-relaxed">
                      {ERROR_DETAILS[customError]?.desc ?? "An unexpected error occurred."}
                    </p>
                    <Button variant="outline" size="sm" className="mt-4" onClick={fetchStatus}>
                      Retry Connection
                    </Button>
                  </div>
                )}

                {/* HUD */}
                <div className="absolute top-3 left-3 text-[10px] font-mono text-brand-cyan bg-navy-darker/80 px-2 py-1 rounded border border-navy-accent/40 pointer-events-none flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />
                  <span>● REC · {status?.fps ?? 0} FPS · Latency: 12ms · Signal: Excellent</span>
                </div>
                <div className="absolute top-3 right-3 text-[10px] font-mono text-slate-400 bg-navy-darker/80 px-2 py-1 rounded border border-navy-accent/40 pointer-events-none">
                  {status?.connected ? `${status.width}×${status.height}` : "OFFLINE"}
                </div>
                <div className="absolute bottom-3 left-3 text-[10px] font-mono text-emerald-400 bg-navy-darker/80 px-2 py-1 rounded border border-navy-accent/40 pointer-events-none">
                  {status?.connected ? `ByteTrack · ${trk?.active_tracks ?? 0} active · ${trk?.unique_ids_seen ?? 0} unique IDs` : "Waiting for active feed..."}
                </div>
              </div>

              {/* Action bar */}
              <div className="flex flex-wrap items-center justify-between gap-4 mt-4">
                <div className="flex gap-2.5">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => alert("Snapshot — not yet implemented.")}
                    disabled={!status?.connected}
                  >
                    📸 Snapshot
                  </Button>
                  <Button variant="outline" size="sm" onClick={toggleFullscreen}>
                    {fullscreen ? "⬜ Exit Fullscreen" : "📺 Fullscreen"}
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setStreamKey(Date.now())}>
                    🔄 Refresh
                  </Button>
                </div>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={handleDisconnect}
                  disabled={!status?.connected}
                >
                  Disconnect Feed
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column ────────────────────────────────────────────────────── */}
        <div className="space-y-5">

          {/* Stream Controls */}
          <Card>
            <CardHeader>
              <CardTitle>Stream Controls</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleConnect} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Source Type
                  </label>
                  <select
                    value={sourceType}
                    onChange={(e) => {
                      setSourceType(e.target.value);
                      setSourceInput(
                        e.target.value === "Webcam" ? "0"
                        : e.target.value === "Video File" ? "assets/traffic.mp4"
                        : "rtsp://"
                      );
                    }}
                    className="w-full bg-navy-dark border border-navy-accent/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-cyan"
                  >
                    <option value="Webcam">Webcam / Index</option>
                    <option value="Video File">Local Video File</option>
                    <option value="RTSP">RTSP Camera</option>
                    <option value="IP Camera">IP Network Camera</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Source Value
                  </label>
                  <input
                    type="text"
                    value={sourceInput}
                    onChange={(e) => setSourceInput(e.target.value)}
                    placeholder={sourceType === "Webcam" ? "Camera index, e.g. 0" : "URL or file path"}
                    className="w-full bg-navy-dark border border-navy-accent/50 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-brand-cyan"
                    required
                  />
                </div>
                <Button
                  variant="primary"
                  type="submit"
                  className="w-full"
                  disabled={connecting || !backendOnline}
                >
                  {connecting ? "Connecting…" : "Connect Camera"}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Helmet Statistics */}
          <Card>
            <CardHeader><CardTitle>Helmet Detection Stats</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  {
                    label: "Helmet Count",
                    val: status?.helmet_stats?.helmet_count ?? 0,
                    cls: "text-status-green font-semibold",
                  },
                  {
                    label: "No Helmet Count",
                    val: status?.helmet_stats?.no_helmet_count ?? 0,
                    cls: (status?.helmet_stats?.no_helmet_count ?? 0) > 0 ? "text-status-red font-semibold" : "text-slate-400",
                  },
                  {
                    label: "Detection Status",
                    val: status?.helmet_stats?.detection_status ?? "Inactive",
                    cls: status?.helmet_stats?.detection_status === "Active" ? "text-status-green" : "text-slate-400",
                  },
                  {
                    label: "Model Status",
                    val: status?.helmet_stats?.model_status ?? "Not Loaded",
                    cls: status?.helmet_stats?.model_status === "Loaded" ? "text-brand-cyan" : "text-status-red",
                  },
                  {
                    label: "Training Status",
                    val: status?.helmet_stats?.training_status ?? "Not Trained",
                    cls: "text-slate-300",
                  },
                ].map(({ label, val, cls }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className={cls}>{val}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Seat Belt Statistics */}
          <Card>
            <CardHeader><CardTitle>Seat Belt Detection Stats</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  {
                    label: "Seat Belt Count",
                    val: status?.seat_belt_stats?.seat_belt_count ?? 0,
                    cls: "text-status-green font-semibold",
                  },
                  {
                    label: "No Seat Belt Count",
                    val: status?.seat_belt_stats?.no_seat_belt_count ?? 0,
                    cls: (status?.seat_belt_stats?.no_seat_belt_count ?? 0) > 0 ? "text-status-red font-semibold" : "text-slate-400",
                  },
                  {
                    label: "Unknown Count",
                    val: status?.seat_belt_stats?.unknown_count ?? 0,
                    cls: "text-slate-400 font-mono",
                  },
                  {
                    label: "Detection Status",
                    val: status?.seat_belt_stats?.detection_status ?? "Inactive",
                    cls: status?.seat_belt_stats?.detection_status === "Active" ? "text-status-green" : "text-slate-400",
                  },
                  {
                    label: "Model Status",
                    val: status?.seat_belt_stats?.model_status ?? "Not Loaded",
                    cls: status?.seat_belt_stats?.model_status === "Loaded" ? "text-brand-cyan" : "text-status-red",
                  },
                  {
                    label: "Training Status",
                    val: status?.seat_belt_stats?.training_status ?? "Not Trained",
                    cls: "text-slate-300",
                  },
                ].map(({ label, val, cls }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className={cls}>{val}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Mobile Phone Statistics */}
          <Card>
            <CardHeader><CardTitle>Mobile Phone Detection Stats</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  {
                    label: "Phone Count",
                    val: status?.mobile_phone_stats?.phone_count ?? 0,
                    cls: (status?.mobile_phone_stats?.phone_count ?? 0) > 0 ? "text-status-red font-semibold" : "text-status-green",
                  },
                  {
                    label: "No Phone Count",
                    val: status?.mobile_phone_stats?.no_phone_count ?? 0,
                    cls: "text-status-green font-semibold",
                  },
                  {
                    label: "Unknown Count",
                    val: status?.mobile_phone_stats?.unknown_count ?? 0,
                    cls: "text-slate-400 font-mono",
                  },
                  {
                    label: "Detection Status",
                    val: status?.mobile_phone_stats?.detection_status ?? "Inactive",
                    cls: status?.mobile_phone_stats?.detection_status === "Active" ? "text-status-green" : "text-slate-400",
                  },
                  {
                    label: "Model Status",
                    val: status?.mobile_phone_stats?.model_status ?? "Not Loaded",
                    cls: status?.mobile_phone_stats?.model_status === "Loaded" ? "text-brand-cyan" : "text-status-red",
                  },
                  {
                    label: "Training Status",
                    val: status?.mobile_phone_stats?.training_status ?? "Not Trained",
                    cls: "text-slate-300",
                  },
                ].map(({ label, val, cls }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className={cls}>{val}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Traffic Signal Statistics */}
          <Card>
            <CardHeader><CardTitle>Traffic Signal Detection Stats</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  {
                    label: "Red Signals",
                    val: status?.traffic_signal_stats?.red_count ?? 0,
                    cls: "text-status-red font-semibold",
                  },
                  {
                    label: "Yellow Signals",
                    val: status?.traffic_signal_stats?.yellow_count ?? 0,
                    cls: "text-brand-orange font-semibold",
                  },
                  {
                    label: "Green Signals",
                    val: status?.traffic_signal_stats?.green_count ?? 0,
                    cls: "text-status-green font-semibold",
                  },
                  {
                    label: "Unknown Count",
                    val: status?.traffic_signal_stats?.unknown_count ?? 0,
                    cls: "text-slate-400 font-mono",
                  },
                  {
                    label: "Detection Status",
                    val: status?.traffic_signal_stats?.detection_status ?? "Inactive",
                    cls: status?.traffic_signal_stats?.detection_status === "Active" ? "text-status-green" : "text-slate-400",
                  },
                  {
                    label: "Model Status",
                    val: status?.traffic_signal_stats?.model_status ?? "Not Loaded",
                    cls: status?.traffic_signal_stats?.model_status === "Loaded" ? "text-brand-cyan" : "text-status-red",
                  },
                  {
                    label: "Training Status",
                    val: status?.traffic_signal_stats?.training_status ?? "Not Trained",
                    cls: "text-slate-300",
                  },
                ].map(({ label, val, cls }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className={cls}>{val}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Wrong Side Statistics */}
          <Card>
            <CardHeader><CardTitle>Wrong Side Detection Stats</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  {
                    label: "Wrong Side Count",
                    val: status?.wrong_side_stats?.wrong_side_count ?? 0,
                    cls: (status?.wrong_side_stats?.wrong_side_count ?? 0) > 0 ? "text-status-red font-semibold animate-pulse" : "text-status-green",
                  },
                  {
                    label: "Correct Direction",
                    val: status?.wrong_side_stats?.correct_direction_count ?? 0,
                    cls: "text-status-green font-semibold",
                  },
                  {
                    label: "Unknown Count",
                    val: status?.wrong_side_stats?.unknown_count ?? 0,
                    cls: "text-slate-400 font-mono",
                  },
                  {
                    label: "Detection Status",
                    val: status?.wrong_side_stats?.detection_status ?? "Inactive",
                    cls: status?.wrong_side_stats?.detection_status === "Active" ? "text-status-green" : "text-slate-400",
                  },
                  {
                    label: "Model Status",
                    val: status?.wrong_side_stats?.model_status ?? "Not Loaded",
                    cls: status?.wrong_side_stats?.model_status === "Loaded" ? "text-brand-cyan" : "text-status-red",
                  },
                  {
                    label: "Training Status",
                    val: status?.wrong_side_stats?.training_status ?? "Not Trained",
                    cls: "text-slate-300",
                  },
                ].map(({ label, val, cls }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className={cls}>{val}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Triple Riding Statistics */}
          <Card>
            <CardHeader><CardTitle>Triple Riding Detection Stats</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  {
                    label: "Single Rider Count",
                    val: status?.triple_riding_stats?.single_rider_count ?? 0,
                    cls: "text-status-green font-semibold",
                  },
                  {
                    label: "Double Riding Count",
                    val: status?.triple_riding_stats?.double_riding_count ?? 0,
                    cls: "text-brand-orange font-semibold",
                  },
                  {
                    label: "Triple Riding Count",
                    val: status?.triple_riding_stats?.triple_riding_count ?? 0,
                    cls: (status?.triple_riding_stats?.triple_riding_count ?? 0) > 0 ? "text-status-red font-semibold animate-pulse" : "text-slate-300",
                  },
                  {
                    label: "Unknown Count",
                    val: status?.triple_riding_stats?.unknown_count ?? 0,
                    cls: "text-slate-400 font-mono",
                  },
                  {
                    label: "Detection Status",
                    val: status?.triple_riding_stats?.detection_status ?? "Inactive",
                    cls: status?.triple_riding_stats?.detection_status === "Active" ? "text-status-green" : "text-slate-400",
                  },
                  {
                    label: "Model Status",
                    val: status?.triple_riding_stats?.model_status ?? "Not Loaded",
                    cls: status?.triple_riding_stats?.model_status === "Loaded" ? "text-brand-cyan" : "text-status-red",
                  },
                  {
                    label: "Association Status",
                    val: status?.triple_riding_stats?.association_status ?? "Inactive",
                    cls: status?.triple_riding_stats?.association_status === "Active" ? "text-status-green" : "text-slate-400",
                  },
                ].map(({ label, val, cls }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className={cls}>{val}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Number Plate Detection (ANPR Stage 1) */}
          <Card>
            <CardHeader><CardTitle>Number Plate Detection Stats</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  {
                    label: "Detecting Plates",
                    val: status?.number_plate_stats?.detecting_count ?? 0,
                    cls: "text-brand-orange font-semibold",
                  },
                  {
                    label: "Stable Plates",
                    val: status?.number_plate_stats?.stable_count ?? 0,
                    cls: "text-status-green font-semibold",
                  },
                  {
                    label: "Crop Ready Count",
                    val: status?.number_plate_stats?.crop_ready_count ?? 0,
                    cls: "text-brand-cyan font-semibold",
                  },
                  {
                    label: "Unknown Plates",
                    val: status?.number_plate_stats?.unknown_count ?? 0,
                    cls: "text-slate-400 font-mono",
                  },
                  {
                    label: "Detection Status",
                    val: status?.number_plate_stats?.detection_status ?? "Inactive",
                    cls: status?.number_plate_stats?.detection_status === "Active" ? "text-status-green" : "text-slate-400",
                  },
                  {
                    label: "Model Status",
                    val: status?.number_plate_stats?.model_status ?? "Not Loaded",
                    cls: status?.number_plate_stats?.model_status === "Loaded" ? "text-brand-cyan" : "text-status-red",
                  },
                ].map(({ label, val, cls }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className={cls}>{val}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* OCR Recognition (ANPR Stage 2) */}
          <Card>
            <CardHeader><CardTitle>OCR Recognition Stats</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  {
                    label: "OCR Requests",
                    val: status?.ocr_stats?.requests_count ?? 0,
                    cls: "text-brand-cyan font-semibold",
                  },
                  {
                    label: "Verified Plates",
                    val: status?.ocr_stats?.verified_count ?? 0,
                    cls: "text-status-green font-semibold",
                  },
                  {
                    label: "Rejected OCR",
                    val: status?.ocr_stats?.rejected_count ?? 0,
                    cls: "text-status-red font-semibold",
                  },
                  {
                    label: "Average Confidence",
                    val: `${status?.ocr_stats?.avg_confidence ? Math.round(status.ocr_stats.avg_confidence) : 0}%`,
                    cls: "text-brand-orange font-mono font-semibold",
                  },
                  {
                    label: "Recognition Status",
                    val: status?.ocr_stats?.detection_status ?? "Inactive",
                    cls: status?.ocr_stats?.detection_status === "Active" ? "text-status-green" : "text-slate-400",
                  },
                  {
                    label: "OCR Engine",
                    val: status?.ocr_stats?.engine_name ?? "easyocr",
                    cls: "text-brand-cyan uppercase font-semibold",
                  },
                ].map(({ label, val, cls }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className={cls}>{val}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Camera Diagnostics */}
          <Card>
            <CardHeader><CardTitle>Camera Diagnostics</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  {
                    label: "Connection",
                    val: status?.connected ? "Connected" : "Disconnected",
                    cls: status?.connected ? "text-status-green font-semibold" : "text-status-red",
                  },
                  { label: "Stream FPS",    val: status?.fps ? `${status.fps} fps` : "—", cls: "text-slate-200 font-mono font-semibold" },
                  { label: "Resolution",    val: status?.connected ? `${status.width}×${status.height}` : "—", cls: "text-slate-200 font-mono" },
                  { label: "Source Type",   val: status?.source_type ?? "—", cls: "text-slate-200" },
                  { label: "Dropped Frames",val: String(status?.dropped_frames ?? 0), cls: "text-slate-200 font-mono" },
                  { label: "Reconnects",    val: String(status?.reconnect_attempts ?? 0), cls: "text-slate-200 font-mono" },
                ].map(({ label, val, cls }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className={cls}>{val}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Model & Tracker Info */}
          <Card>
            <CardHeader><CardTitle>Pipeline Config</CardTitle></CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-navy-accent/20 text-xs">
                {[
                  { label: "Detector",    value: "YOLOv8n" },
                  { label: "Tracker",     value: "ByteTrack" },
                  { label: "Library",     value: "supervision 0.29" },
                  { label: "Classes",     value: "6 vehicle types" },
                  { label: "Backend",     value: "CPU / PyTorch" },
                  { label: "Render",      value: "Server-side MJPEG" },
                ].map(({ label, value }) => (
                  <div key={label} className="px-5 py-2.5 flex justify-between">
                    <span className="text-slate-400">{label}</span>
                    <span className="text-brand-cyan font-mono">{value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

        </div>
      </div>
    </div>
  );
}

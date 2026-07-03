import React, { useState, useEffect, useRef, useContext } from "react";
import { AuthContext } from "../App";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { motion, AnimatePresence } from "framer-motion";
import {
  Radio,
  Search,
  SlidersHorizontal,
  Maximize2,
  Minimize2,
  Video,
  VideoOff,
  AlertTriangle,
  Car,
  Activity,
  Heart,
  Camera as CameraIcon,
  ShieldCheck,
  Zap,
  Info,
  Clock,
  MapPin,
  X
} from "lucide-react";

interface CameraStream {
  id: string
  name: string
  location: string
  status: "online" | "offline"
  health: "good" | "warning" | "critical"
  vehicles_count: number
  violations_count: number
  ip_address: string
  lat: number
  lng: number
}

// Full mock data matching the requirements
const initialCameras: CameraStream[] = [
  { id: "CAM-001", name: "Connaught Place Jn 1", location: "Outer Ring Road, Connaught Place", status: "online", health: "good", vehicles_count: 1420, violations_count: 32, ip_address: "192.168.10.51", lat: 28.6304, lng: 77.2177 },
  { id: "CAM-002", name: "India Gate Circular 3", location: "India Gate Radial Road", status: "online", health: "good", vehicles_count: 980, violations_count: 18, ip_address: "192.168.10.52", lat: 28.6129, lng: 77.2295 },
  { id: "CAM-003", name: "Rajouri Garden Flyover", location: "Rajouri Garden Intersection", status: "online", health: "warning", vehicles_count: 670, violations_count: 24, ip_address: "192.168.10.53", lat: 28.6415, lng: 77.1245 },
  { id: "CAM-004", name: "AIIMS Crossing Main Feed", location: "Ring Road Interchange", status: "offline", health: "critical", vehicles_count: 0, violations_count: 0, ip_address: "192.168.10.54", lat: 28.5672, lng: 77.2100 },
  { id: "CAM-005", name: "Karol Bagh Bazar CCTV 3", location: "Bazar Crossing, Karol Bagh", status: "online", health: "good", vehicles_count: 420, violations_count: 9, ip_address: "192.168.10.55", lat: 28.6441, lng: 77.1895 },
  { id: "CAM-006", name: "Lajpat Nagar Flyover", location: "Lajpat Nagar Ring Road", status: "online", health: "good", vehicles_count: 1120, violations_count: 15, ip_address: "192.168.10.56", lat: 28.5708, lng: 77.2418 }
];

export default function LiveMonitoring() {
  const [cameras, setCameras] = useState<CameraStream[]>(initialCameras);
  const [selectedCam, setSelectedCam] = useState<CameraStream>(initialCameras[0]);
  
  // Searching & Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [healthFilter, setHealthFilter] = useState("all");
  
  // Custom Overlays
  const [showLanes, setShowLanes] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [logs, setLogs] = useState<{ time: string; text: string; error?: boolean }[]>([]);
  
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);

  // Increment simulated vehicle telemetry counts over time
  useEffect(() => {
    const timer = setInterval(() => {
      setCameras((prev) =>
        prev.map((c) => {
          if (c.status === "offline") return c;
          const newVehicles = Math.random() < 0.7 ? 1 : 0;
          const newViolations = Math.random() < 0.05 ? 1 : 0;
          return {
            ...c,
            vehicles_count: c.vehicles_count + newVehicles,
            violations_count: c.violations_count + newViolations
          };
        })
      );
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  // Update selected camera reference details dynamically when stats change
  useEffect(() => {
    const updated = cameras.find((c) => c.id === selectedCam.id);
    if (updated) {
      setSelectedCam(updated);
    }
  }, [cameras, selectedCam.id]);

  // Log Ticker generator
  useEffect(() => {
    if (!selectedCam) return;
    
    setLogs([
      { time: new Date().toLocaleTimeString(), text: `Connecting to camera stream link ${selectedCam.id}...` },
      { time: new Date().toLocaleTimeString(), text: `AI engine initialized for lane detection & object tracking.` }
    ]);

    const plateStates = ["DL", "MH", "KA", "HR", "UP"];
    const vTypes = ["Car", "Motorcycle", "Truck", "Bus", "Auto"];

    const interval = setInterval(() => {
      if (selectedCam.status === "offline") return;
      const time = new Date().toLocaleTimeString();
      const type = vTypes[Math.floor(Math.random() * vTypes.length)];
      const plate = `${plateStates[Math.floor(Math.random() * plateStates.length)]} ${Math.floor(Math.random() * 99) + 1} ${String.fromCharCode(65 + Math.floor(Math.random() * 26))}${String.fromCharCode(65 + Math.floor(Math.random() * 26))} ${Math.floor(Math.random() * 8900) + 1000}`;
      const speed = Math.floor(Math.random() * 55) + 30;

      let logText = `${type} detected (Plate: ${plate}) | Speed: ${speed} km/h`;
      let isViolation = false;

      if (Math.random() < 0.2) {
        isViolation = true;
        const violations = [
          "Overspeeding (" + (speed + 20) + " km/h - Limit: 60)",
          "Stop Line Crossing",
          "Wrong Lane Driving",
          "Red Light Jump"
        ];
        logText = `⚠️ INCIDENT! ${violations[Math.floor(Math.random() * violations.length)]} by ${type} (${plate}). Fine generated.`;
      }

      setLogs((prev) => [
        { time, text: logText, error: isViolation },
        ...prev.slice(0, 15)
      ]);
    }, 6000);

    return () => clearInterval(interval);
  }, [selectedCam.id]);

  // HTML5 Canvas Traffic drawing loop
  useEffect(() => {
    if (!canvasRef.current || !selectedCam || selectedCam.status !== "online") return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = 800;
    canvas.height = 450;

    let signal = "green";
    let timer = 0;

    let vehicles = [
      { id: 1, x: 50, y: 150, speed: 2.5, type: "Car", plate: "DL 3C AB 9081", color: "#3b82f6", width: 62, height: 35, committed: false },
      { id: 2, x: 300, y: 240, speed: 1.8, type: "Truck", plate: "MH 12 RN 4567", color: "#64748b", width: 88, height: 46, committed: false },
      { id: 3, x: 600, y: 190, speed: 2.8, type: "Motorcycle", plate: "KA 05 XY 5678", color: "#f59e0b", width: 42, height: 22, committed: false }
    ];

    const colorsList = ["#3b82f6", "#10b981", "#ef4444", "#8b5cf6", "#f59e0b"];
    const typesList = ["Car", "Motorcycle", "Truck", "Auto"];

    const draw = () => {
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Roads
      ctx.fillStyle = "#1e293b";
      ctx.fillRect(0, 100, canvas.width, 250);

      // Lane dividers (Draw only if showLanes overlay is active)
      if (showLanes) {
        ctx.strokeStyle = "#475569";
        ctx.lineWidth = 4;
        ctx.setLineDash([20, 15]);
        ctx.beginPath();
        ctx.moveTo(0, 180); ctx.lineTo(canvas.width, 180);
        ctx.moveTo(0, 270); ctx.lineTo(canvas.width, 270);
        ctx.stroke();
        ctx.setLineDash([]);
        
        // Target lanes highlighting
        ctx.fillStyle = "rgba(59, 130, 246, 0.05)";
        ctx.fillRect(0, 180, canvas.width, 90); // middle lane
      }

      // Stop Line
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.moveTo(600, 100); ctx.lineTo(600, 350);
      ctx.stroke();

      // Signals switching
      timer++;
      if (timer > 220) {
        signal = signal === "green" ? "yellow" : signal === "yellow" ? "red" : "green";
        timer = 0;
      }

      ctx.fillStyle = "#334155";
      ctx.fillRect(630, 40, 15, 60);

      ctx.beginPath();
      ctx.arc(637, 50, 4, 0, Math.PI * 2);
      ctx.fillStyle = signal === "red" ? "#ef4444" : "#1e293b";
      ctx.fill();

      ctx.beginPath();
      ctx.arc(637, 70, 4, 0, Math.PI * 2);
      ctx.fillStyle = signal === "yellow" ? "#eab308" : "#1e293b";
      ctx.fill();

      ctx.beginPath();
      ctx.arc(637, 90, 4, 0, Math.PI * 2);
      ctx.fillStyle = signal === "green" ? "#22c55e" : "#1e293b";
      ctx.fill();

      // HUD HUD
      ctx.fillStyle = "rgba(0,0,0,0.5)";
      ctx.fillRect(15, 15, 230, 70);
      ctx.strokeStyle = "rgba(59,130,246,0.3)";
      ctx.strokeRect(15, 15, 230, 70);

      ctx.fillStyle = "#60a5fa";
      ctx.font = "bold 10px Courier New";
      ctx.fillText(`CAM: ${selectedCam.id}`, 25, 30);
      ctx.fillText(`GPS: ${selectedCam.lat.toFixed(4)},${selectedCam.lng.toFixed(4)}`, 25, 45);
      ctx.fillText(`PIPELINE: ACTIVE_YOLO8`, 25, 60);

      // Vehicles movement
      vehicles.forEach((v) => {
        const close = v.x + v.width > 550 && v.x < 590;
        if (signal === "red" && close) {
          if (v.id === 1 && Math.random() < 0.005) {
            v.committed = true;
          }
          if (!v.committed) {
            v.speed = Math.max(0, v.speed - 0.25);
          }
        } else {
          v.speed = Math.min(v.speed + 0.1, v.id === 1 ? 2.6 : 1.8);
        }

        v.x += v.speed;
        if (v.x > canvas.width) {
          v.x = -100;
          v.committed = false;
          v.color = colorsList[Math.floor(Math.random() * colorsList.length)];
          v.type = typesList[Math.floor(Math.random() * typesList.length)];
        }

        ctx.fillStyle = v.color;
        ctx.fillRect(v.x, v.y, v.width, v.height);

        const viol = v.committed || (v.id === 1 && v.speed > 2.2);
        ctx.strokeStyle = viol ? "#ef4444" : "#22c55e";
        ctx.lineWidth = 2;
        ctx.strokeRect(v.x - 3, v.y - 3, v.width + 6, v.height + 6);

        ctx.fillStyle = viol ? "#ef4444" : "#22c55e";
        ctx.font = "bold 9px Arial";
        ctx.fillText(`${v.type.toUpperCase()} [${v.plate}]`, v.x, v.y - 8);
      });

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [selectedCam.id, showLanes]);

  // Filtering Logic
  const filteredCameras = cameras.filter((cam) => {
    const matchesSearch =
      cam.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      cam.location.toLowerCase().includes(searchQuery.toLowerCase());
      
    const matchesStatus =
      statusFilter === "all" || cam.status === statusFilter;
      
    const matchesHealth =
      healthFilter === "all" || cam.health === healthFilter;

    return matchesSearch && matchesStatus && matchesHealth;
  });

  return (
    <div className="space-y-6 relative">
      
      {/* Fullscreen Canvas Overlay Modal */}
      <AnimatePresence>
        {isFullscreen && selectedCam.status === "online" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-slate-950 flex flex-col justify-between p-4"
          >
            <div className="flex justify-between items-center text-white px-2">
              <div>
                <strong className="text-sm block">{selectedCam.name} (FULLSCREEN)</strong>
                <span className="text-[10px] text-slate-400">{selectedCam.location}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsFullscreen(false)}
                className="h-8 py-1 border-white/20 text-white hover:bg-white/10"
              >
                <Minimize2 size={14} className="mr-1.5" /> Close Fullscreen
              </Button>
            </div>
            
            <div className="flex-1 flex items-center justify-center p-4">
              <canvas
                ref={(el) => {
                  if (el) {
                    const ctx = el.getContext("2d");
                    if (ctx) {
                      el.width = 1280;
                      el.height = 720;
                      // Draw loop maps to standard frame
                      const drawFs = () => {
                        if (!isFullscreen) return;
                        ctx.fillStyle = "#0f172a";
                        ctx.fillRect(0, 0, el.width, el.height);
                        ctx.fillStyle = "#1e293b";
                        ctx.fillRect(0, 200, el.width, 350);
                        ctx.strokeStyle = "#475569";
                        ctx.lineWidth = 4;
                        ctx.strokeRect(0, 200, el.width, 350);
                        ctx.fillStyle = "#60a5fa";
                        ctx.font = "bold 20px Courier New";
                        ctx.fillText(`CAM: ${selectedCam.id} | FULLSCREEN CHECK`, 50, 50);
                      };
                      drawFs();
                    }
                  }
                }}
                className="w-full max-h-[85vh] rounded-2xl border border-slate-800 bg-slate-900"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">CCTV Command Room</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Live sensor coordinate matrices, camera checkers, and real-time alerts tickers.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        
        {/* Left Side: Search & Cards list */}
        <div className="xl:col-span-1 space-y-6">
          <Card className="glass-card p-4 space-y-4">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <SlidersHorizontal size={14} className="text-blue-500" />
              Sensor Filters
            </CardTitle>
            
            {/* Search Input */}
            <div className="relative">
              <Search size={14} className="absolute left-3 top-3 text-slate-400" />
              <Input
                type="text"
                placeholder="Search camera or location..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 text-xs h-9"
              />
            </div>

            {/* Dropdowns */}
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">Connection Status</label>
                <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="h-9 text-xs">
                  <option value="all">All Statuses</option>
                  <option value="online">Online</option>
                  <option value="offline">Offline</option>
                </Select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">Diagnostic Health</label>
                <Select value={healthFilter} onChange={(e) => setHealthFilter(e.target.value)} className="h-9 text-xs">
                  <option value="all">All Health Tiers</option>
                  <option value="good">Good Health</option>
                  <option value="warning">Warning status</option>
                  <option value="critical">Critical Faults</option>
                </Select>
              </div>
            </div>
          </Card>

          {/* Camera cards list (Scrollable) */}
          <div className="space-y-3.5 max-h-[480px] overflow-y-auto pr-1">
            {filteredCameras.map((cam) => {
              const isSelected = selectedCam.id === cam.id;
              return (
                <motion.div
                  whileHover={{ y: -2 }}
                  key={cam.id}
                  onClick={() => setSelectedCam(cam)}
                  className={`p-4 rounded-2xl border transition-all duration-150 flex flex-col justify-between gap-3 cursor-pointer ${
                    isSelected
                      ? "border-blue-500 bg-blue-600/10 shadow-lg shadow-blue-500/5"
                      : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950/60 hover:bg-slate-100/50 dark:hover:bg-slate-900/60"
                  }`}
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <Badge variant="secondary" className="text-[9px] px-1.5 py-0">
                        {cam.id}
                      </Badge>
                      <div className="flex items-center gap-1.5 text-[9px] font-bold">
                        <span className={`h-1.5 w-1.5 rounded-full ${cam.status === "online" ? "bg-emerald-500" : "bg-red-500"}`} />
                        <span className="uppercase text-slate-400">{cam.status}</span>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-extrabold text-xs truncate">{cam.name}</h3>
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 font-semibold flex items-center gap-1 mt-0.5">
                        <MapPin size={10} className="shrink-0" />
                        {cam.location}
                      </span>
                    </div>
                  </div>

                  {/* Card Mini Telemetry Stats */}
                  <div className="grid grid-cols-3 gap-1.5 text-[9px] font-bold border-t border-slate-150/30 dark:border-slate-850/40 pt-2.5">
                    <div>
                      <span className="text-slate-400 block uppercase">Vehicles</span>
                      <span>{cam.vehicles_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block uppercase">Violations</span>
                      <span className={cam.violations_count > 20 ? "text-red-500" : ""}>{cam.violations_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block uppercase">Health</span>
                      <span className={
                        cam.health === "good" ? "text-emerald-500" : cam.health === "warning" ? "text-amber-500" : "text-red-500"
                      }>
                        {cam.health.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Right Side: Monitor Viewport, Ticker logs & Mini-grid */}
        <div className="xl:col-span-3 space-y-6">
          <Card className="glass-card p-4 overflow-hidden border-slate-200/50 dark:border-slate-800/50 shadow-lg">
            
            {/* Main Monitor Screen */}
            <div className="relative">
              {selectedCam.status === "online" ? (
                <canvas
                  ref={canvasRef}
                  className="w-full aspect-video rounded-xl border border-slate-200 dark:border-slate-850 bg-slate-900"
                />
              ) : (
                <div className="w-full aspect-video rounded-xl bg-slate-900 border border-slate-850 flex flex-col items-center justify-center text-center p-6 gap-3">
                  <div className="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 border border-red-500/20 animate-pulse">
                    <VideoOff size={22} />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-sm">Hardware Link Terminated</h3>
                    <p className="text-xs text-slate-400 max-w-xs mt-1">
                      Stream timeout detected at CAM ID {selectedCam.id}. Verify network link.
                    </p>
                  </div>
                </div>
              )}

              {/* HUD Screen Overlays */}
              <div className="absolute top-4 right-4 flex gap-1.5 z-20">
                <Badge className="bg-black/60 border border-white/10 hover:bg-black/60 flex items-center gap-1.5 py-1 text-[9px] font-bold">
                  <Radio size={10} className="text-red-500 animate-ping" />
                  {selectedCam.status === "online" ? "LIVE FEED" : "FEED OFFLINE"}
                </Badge>
                
                {selectedCam.status === "online" && (
                  <Button
                    onClick={() => setIsFullscreen(true)}
                    variant="secondary"
                    className="bg-black/60 hover:bg-black/80 text-white border border-white/10 h-6 px-2 text-[9px] font-bold"
                  >
                    <Maximize2 size={10} className="mr-1" />
                    Fullscreen
                  </Button>
                )}
              </div>
            </div>

            {/* Viewport Control Panel */}
            {selectedCam.status === "online" && (
              <div className="flex flex-wrap items-center justify-between mt-3 pt-3 border-t border-slate-200/40 dark:border-slate-850/40 gap-4 text-xs font-bold">
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1.5 text-slate-400">
                    <Heart size={14} className="text-red-500 shrink-0 fill-red-500" />
                    Health Tier:
                  </span>
                  <Badge variant={selectedCam.health === "good" ? "success" : "secondary"}>
                    {selectedCam.health}
                  </Badge>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-[10px]"
                    onClick={() => setShowLanes(!showLanes)}
                  >
                    {showLanes ? "Hide Lanes" : "Lanes Overlay"}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-[10px]"
                    onClick={() => alert(`Snapshot captured for checkpoint ${selectedCam.id}`)}
                  >
                    Capture Snapshot
                  </Button>
                </div>
              </div>
            )}
          </Card>

          {/* Incident Telemetry Logs */}
          <Card className="glass-card p-5 space-y-4">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Clock size={16} className="text-blue-500" />
              Telemetry Logs Checklist ({selectedCam.id})
            </CardTitle>
            <div className="h-32 overflow-y-auto font-mono text-[9px] leading-relaxed space-y-2 p-3 rounded-lg bg-slate-900/60 dark:bg-slate-950/60 border border-slate-300/10">
              {logs.map((log, idx) => (
                <div key={idx} className={`flex gap-3 ${log.error ? "text-red-400 font-bold" : "text-slate-350"}`}>
                  <span className="text-slate-500 shrink-0">[{log.time}]</span>
                  <span>{log.text}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}

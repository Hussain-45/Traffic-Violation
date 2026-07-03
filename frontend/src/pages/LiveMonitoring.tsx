import React, { useState, useEffect, useRef, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog";
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
  Camera as CameraIcon,
  ShieldCheck,
  Zap,
  Clock,
  MapPin,
  Plus,
  Tv,
  Globe,
  Settings
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
  stream_type: "simulated" | "webcam" | "rtsp"
  rtsp_url?: string
}

// Initial seeder cameras
const initialCameras: CameraStream[] = [
  { id: "CAM-001", name: "Connaught Place Outer Ring", location: "Outer Ring Road, Connaught Place", status: "online", health: "good", vehicles_count: 42, violations_count: 5, ip_address: "192.168.10.51", stream_type: "simulated" },
  { id: "CAM-002", name: "India Gate Circle", location: "India Gate Radial Road", status: "online", health: "good", vehicles_count: 28, violations_count: 2, ip_address: "192.168.10.52", stream_type: "simulated" },
  { id: "CAM-003", name: "Rajouri Garden Flyover", location: "Rajouri Garden Intersection", status: "online", health: "warning", vehicles_count: 31, violations_count: 4, ip_address: "192.168.10.53", stream_type: "simulated" },
  { id: "CAM-004", name: "AIIMS Crossing Main Feed", location: "Ring Road Interchange", status: "offline", health: "critical", vehicles_count: 0, violations_count: 0, ip_address: "192.168.10.54", stream_type: "simulated" },
  { id: "CAM-005", name: "Karol Bagh Bazar CCTV 3", location: "Bazar Crossing, Karol Bagh", status: "online", health: "good", vehicles_count: 19, violations_count: 1, ip_address: "192.168.10.55", stream_type: "simulated" }
];

export default function LiveMonitoring() {
  const { token } = useContext(AuthContext);
  const [cameras, setCameras] = useState<CameraStream[]>(initialCameras);
  const [selectedCam, setSelectedCam] = useState<CameraStream>(initialCameras[0]);
  
  // Search & Filter options
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  
  // Custom states
  const [showLanes, setShowLanes] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [logs, setLogs] = useState<{ time: string; text: string; error?: boolean }[]>([]);
  const [fps, setFps] = useState<number>(0);
  
  // Camera addition modal dialog
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newCamName, setNewCamName] = useState("");
  const [newCamLoc, setNewCamLoc] = useState("");
  const [newCamType, setNewCamType] = useState<"simulated" | "webcam" | "rtsp">("simulated");
  const [newCamIp, setNewCamIp] = useState("");
  const [newCamRtsp, setNewCamRtsp] = useState("");

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);

  // Webcam stream elements
  const webcamVideoRef = useRef<HTMLVideoElement | null>(null);
  const webcamStreamRef = useRef<MediaStream | null>(null);

  // FPS calculation references
  const lastFrameTimeRef = useRef<number>(performance.now());
  const frameCountRef = useRef<number>(0);
  const lastFpsUpdateTimeRef = useRef<number>(performance.now());

  // Increment simulated telemetry counts
  useEffect(() => {
    const timer = setInterval(() => {
      setCameras((prev) =>
        prev.map((c) => {
          if (c.status === "offline") return c;
          const deltaVehicles = Math.random() < 0.4 ? 1 : 0;
          const deltaViolations = Math.random() < 0.05 ? 1 : 0;
          return {
            ...c,
            vehicles_count: c.vehicles_count + deltaVehicles,
            violations_count: c.violations_count + deltaViolations
          };
        })
      );
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  // Sync selected camera details when lists update
  useEffect(() => {
    const updated = cameras.find((c) => c.id === selectedCam.id);
    if (updated) setSelectedCam(updated);
  }, [cameras, selectedCam.id]);

  // Initializing webcam media stream if type is webcam
  useEffect(() => {
    const stopWebcam = () => {
      if (webcamStreamRef.current) {
        webcamStreamRef.current.getTracks().forEach((track) => track.stop());
        webcamStreamRef.current = null;
      }
      if (webcamVideoRef.current) {
        webcamVideoRef.current.srcObject = null;
      }
    };

    if (selectedCam.status === "online" && selectedCam.stream_type === "webcam") {
      setLogs([
        { time: new Date().toLocaleTimeString(), text: "Requesting local webcam stream access..." }
      ]);
      
      const initWebcam = async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 1280, height: 720, frameRate: { ideal: 30 } }
          });
          
          webcamStreamRef.current = stream;
          
          if (!webcamVideoRef.current) {
            const videoElement = document.createElement("video");
            videoElement.autoplay = true;
            videoElement.playsInline = true;
            webcamVideoRef.current = videoElement;
          }
          
          webcamVideoRef.current.srcObject = stream;
          webcamVideoRef.current.play();

          setLogs((prev) => [
            { time: new Date().toLocaleTimeString(), text: "Webcam connected successfully. Initializing real-time bounding boxes..." },
            ...prev
          ]);
        } catch (err) {
          console.error("Webcam access error:", err);
          setLogs((prev) => [
            { time: new Date().toLocaleTimeString(), text: "Failed to access webcam. Check browser permissions.", error: true },
            ...prev
          ]);
          // Revert connection
          setSelectedCam(prev => ({ ...prev, status: "offline" }));
        }
      };
      
      initWebcam();
    } else {
      stopWebcam();
    }

    return () => stopWebcam();
  }, [selectedCam.id, selectedCam.status, selectedCam.stream_type]);

  // Telemetry Log Ticker
  useEffect(() => {
    setLogs([
      { time: new Date().toLocaleTimeString(), text: `Connecting to camera node link ${selectedCam.id} (${selectedCam.stream_type.toUpperCase()})...` },
      { time: new Date().toLocaleTimeString(), text: `Configuring YOLOv8 traffic models & OCR diagnostics.` }
    ]);

    if (selectedCam.status === "offline") {
      setLogs((prev) => [
        { time: new Date().toLocaleTimeString(), text: `Connection status: Offline. CCTV stream offline.`, error: true },
        ...prev
      ]);
      return;
    }

    const vTypes = ["Car", "Motorcycle", "Truck", "Bus", "Auto"];
    const plates = ["DL 3C AB 9081", "MH 14 BN 2290", "KA 03 FG 1156", "HR 26 AZ 4545", "UP 16 KL 8890"];
    
    const interval = setInterval(() => {
      if (selectedCam.status === "offline") return;
      const time = new Date().toLocaleTimeString();
      const type = vTypes[Math.floor(Math.random() * vTypes.length)];
      const plate = plates[Math.floor(Math.random() * plates.length)];
      const speed = Math.floor(Math.random() * 55) + 30;

      let logText = `${type} logged (Plate: ${plate}) | Speed: ${speed} km/h`;
      let isViolation = false;

      if (Math.random() < 0.22) {
        isViolation = true;
        const violations = ["Wrong Lane Driving", "Wrong Direction", "Red Light Jump", "Stop Line Crossing", "No Helmet Riding"];
        logText = `⚠️ INCIDENT: ${violations[Math.floor(Math.random() * violations.length)]} by ${type} (${plate}). Fine logged.`;
      }

      setLogs((prev) => [
        { time, text: logText, error: isViolation },
        ...prev.slice(0, 15)
      ]);
    }, 6000);

    return () => clearInterval(interval);
  }, [selectedCam.id, selectedCam.status]);

  // Main Canvas Drawing Loop (Webcam / Simulated streams)
  useEffect(() => {
    if (!canvasRef.current || selectedCam.status !== "online") return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = 800;
    canvas.height = 450;

    let signal = "green";
    let signalTimer = 0;

    // Simulated Bounding Boxes
    let vehicles = [
      { id: 1, x: 50, y: 150, speed: 2.8, type: "Car", plate: "DL 3C AB 9081", color: "#3b82f6", width: 62, height: 35, violating: false },
      { id: 2, x: 300, y: 240, speed: 1.8, type: "Truck", plate: "MH 12 RN 4567", color: "#64748b", width: 88, height: 46, violating: false },
      { id: 3, x: 550, y: 190, speed: 2.2, type: "Auto", plate: "KA 05 XY 5678", color: "#f59e0b", width: 48, height: 32, violating: false }
    ];

    const drawLoop = () => {
      // 1. Draw Stream Source
      if (selectedCam.stream_type === "webcam" && webcamVideoRef.current && webcamVideoRef.current.readyState >= 2) {
        // Draw webcam frames onto canvas
        ctx.drawImage(webcamVideoRef.current, 0, 0, canvas.width, canvas.height);
      } else {
        // Draw standard simulated highway background
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = "#1e293b";
        ctx.fillRect(0, 100, canvas.width, 250);

        if (showLanes) {
          ctx.strokeStyle = "#475569";
          ctx.lineWidth = 3;
          ctx.setLineDash([20, 15]);
          ctx.beginPath();
          ctx.moveTo(0, 180); ctx.lineTo(canvas.width, 180);
          ctx.moveTo(0, 270); ctx.lineTo(canvas.width, 270);
          ctx.stroke();
          ctx.setLineDash([]);
          
          ctx.fillStyle = "rgba(59, 130, 246, 0.05)";
          ctx.fillRect(0, 180, canvas.width, 90);
        }

        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 5;
        ctx.beginPath();
        ctx.moveTo(600, 100); ctx.lineTo(600, 350);
        ctx.stroke();
      }

      // 2. Traffic Signal simulator (drawn for both webcam and simulation models)
      signalTimer++;
      if (signalTimer > 250) {
        signal = signal === "green" ? "yellow" : signal === "yellow" ? "red" : "green";
        signalTimer = 0;
      }

      ctx.fillStyle = "rgba(15, 23, 42, 0.7)";
      ctx.fillRect(canvas.width - 60, 25, 45, 120);
      ctx.strokeStyle = "rgba(255,255,255,0.1)";
      ctx.strokeRect(canvas.width - 60, 25, 45, 120);

      const colors = { red: "#ef4444", yellow: "#f59e0b", green: "#10b981" };
      ctx.beginPath();
      ctx.arc(canvas.width - 38, 45, 10, 0, Math.PI * 2);
      ctx.fillStyle = signal === "red" ? colors.red : "#1e293b";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(canvas.width - 38, 85, 10, 0, Math.PI * 2);
      ctx.fillStyle = signal === "yellow" ? colors.yellow : "#1e293b";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(canvas.width - 38, 125, 10, 0, Math.PI * 2);
      ctx.fillStyle = signal === "green" ? colors.green : "#1e293b";
      ctx.fill();

      // 3. Draw Bounding Boxes overlay
      if (selectedCam.stream_type === "webcam") {
        // Draw mock webcam bounding boxes mapped to webcam centers (keeps HUD dynamic)
        const frameTime = performance.now();
        const cycle = Math.sin(frameTime / 2000) * 120;
        
        ctx.strokeStyle = "#22c55e";
        ctx.lineWidth = 2.5;
        ctx.strokeRect(200 + cycle, 120, 180, 210);
        ctx.fillStyle = "#22c55e";
        ctx.font = "bold 11px monospace";
        ctx.fillText("Person [Conf: 0.94] (0 km/h)", 200 + cycle, 112);

        // Subplate mock over webcam
        ctx.strokeStyle = "#eab308";
        ctx.strokeRect(250 + cycle, 280, 80, 25);
        ctx.fillStyle = "#eab308";
        ctx.font = "bold 9px monospace";
        ctx.fillText("DL 3C AB 9081", 250 + cycle, 275);
      } else {
        // Draw vehicle coordinates movement for simulation
        vehicles.forEach((v) => {
          const checkLine = v.x + v.width > 550 && v.x < 595;
          if (signal === "red" && checkLine) {
            if (v.id === 1 && Math.random() < 0.003) v.violating = true;
            if (!v.violating) v.speed = Math.max(0, v.speed - 0.22);
          } else {
            v.speed = Math.min(v.speed + 0.08, v.id === 1 ? 2.8 : 1.9);
          }

          v.x += v.speed;
          if (v.x > canvas.width) {
            v.x = -110;
            v.violating = false;
          }

          // Bounding Box
          const boxColor = v.violating ? "#ef4444" : "#10b981";
          ctx.strokeStyle = boxColor;
          ctx.lineWidth = 2.5;
          ctx.strokeRect(v.x, v.y, v.width, v.height);

          // Plate crop outline
          ctx.strokeStyle = "#eab308";
          ctx.lineWidth = 1.5;
          ctx.strokeRect(v.x + v.width * 0.25, v.y + v.height * 0.7, v.width * 0.5, v.height * 0.2);

          // Label
          ctx.fillStyle = boxColor;
          ctx.font = "bold 10px monospace";
          ctx.fillText(`${v.type.toUpperCase()} [Conf: 0.91] (${Math.round(v.speed * 25)} km/h)`, v.x, v.y - 7);
        });
      }

      // 4. Calculate real-time FPS
      const now = performance.now();
      frameCountRef.current++;
      
      if (now - lastFpsUpdateTimeRef.current >= 1000) {
        const calculatedFps = Math.round((frameCountRef.current * 1000) / (now - lastFpsUpdateTimeRef.current));
        setFps(calculatedFps);
        frameCountRef.current = 0;
        lastFpsUpdateTimeRef.current = now;
      }
      
      // HUD Overlay details
      ctx.fillStyle = "rgba(15, 23, 42, 0.75)";
      ctx.fillRect(15, 15, 230, 80);
      ctx.strokeStyle = "rgba(59, 130, 246, 0.3)";
      ctx.strokeRect(15, 15, 230, 80);

      ctx.fillStyle = "#60a5fa";
      ctx.font = "bold 10px monospace";
      ctx.fillText(`CAM NODE: ${selectedCam.id}`, 25, 30);
      ctx.fillText(`TYPE: ${selectedCam.stream_type.toUpperCase()}`, 25, 45);
      ctx.fillText(`IP: ${selectedCam.ip_address}`, 25, 60);
      ctx.fillText(`FPS: ${fps} FPS`, 25, 75);

      animationRef.current = requestAnimationFrame(drawLoop);
    };

    drawLoop();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [selectedCam.id, selectedCam.status, selectedCam.stream_type, showLanes, fps]);

  // Handle adding new custom camera link
  const handleAddCamera = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCamName || !newCamLoc) return;

    const newId = `CAM-${String(cameras.length + 1).padStart(3, "0")}`;
    const newStream: CameraStream = {
      id: newId,
      name: newCamName,
      location: newCamLoc,
      status: "online",
      health: "good",
      vehicles_count: 0,
      violations_count: 0,
      ip_address: newCamIp || "192.168.10.8" + (cameras.length + 1),
      stream_type: newCamType,
      rtsp_url: newCamType === "rtsp" ? newCamRtsp : undefined
    };

    setCameras((prev) => [...prev, newStream]);
    setSelectedCam(newStream);
    setIsAddOpen(false);

    // Reset fields
    setNewCamName("");
    setNewCamLoc("");
    setNewCamType("simulated");
    setNewCamIp("");
    setNewCamRtsp("");

    setLogs((prev) => [
      { time: new Date().toLocaleTimeString(), text: `Configured new CCTV camera node ${newId} (${newCamName}).` },
      ...prev
    ]);
  };

  // Toggle Camera Status Online/Offline
  const toggleCameraLink = () => {
    setCameras((prev) =>
      prev.map((c) => {
        if (c.id === selectedCam.id) {
          const nextStatus = c.status === "online" ? "offline" : "online";
          const nextHealth = nextStatus === "offline" ? "critical" : "good";
          return { ...c, status: nextStatus, health: nextHealth };
        }
        return c;
      })
    );
  };

  // Filter cameras based on search and status
  const filteredCams = cameras.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.location.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      
      {/* Add CCTV Stream Modal */}
      <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
        <DialogContent className="glass-card max-w-md text-slate-100 p-6 border-slate-800">
          <DialogHeader>
            <DialogTitle className="text-sm font-extrabold uppercase tracking-wider text-slate-400">
              Register CCTV Camera Node
            </DialogTitle>
            <DialogDescription className="text-[10px] text-slate-500 font-semibold">
              Link RTSP streams, IP cameras, or webcams to the AI detection grid.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleAddCamera} className="space-y-4 my-3 text-xs">
            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-400 uppercase">Camera Node Name</label>
              <Input
                value={newCamName}
                onChange={(e) => setNewCamName(e.target.value)}
                placeholder="e.g. Lajpat Nagar Ring Road"
                required
                className="h-9 text-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-400 uppercase">Junction Location</label>
              <Input
                value={newCamLoc}
                onChange={(e) => setNewCamLoc(e.target.value)}
                placeholder="e.g. Radial Road Intersection"
                required
                className="h-9 text-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">Stream Source Type</label>
                <Select
                  value={newCamType}
                  onChange={(e: any) => setNewCamType(e.target.value)}
                  className="h-9 text-xs"
                >
                  <option value="simulated">Demo Simulator</option>
                  <option value="webcam">Local Web Camera</option>
                  <option value="rtsp">RTSP CCTV Feed</option>
                </Select>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">IP Address</label>
                <Input
                  value={newCamIp}
                  onChange={(e) => setNewCamIp(e.target.value)}
                  placeholder="e.g. 192.168.10.60"
                  className="h-9 text-xs"
                />
              </div>
            </div>

            {newCamType === "rtsp" && (
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">RTSP Feed URL</label>
                <Input
                  value={newCamRtsp}
                  onChange={(e) => setNewCamRtsp(e.target.value)}
                  placeholder="rtsp://admin:pass@ip:port/h264"
                  className="h-9 text-xs"
                />
              </div>
            )}

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsAddOpen(false)}
                className="h-9 text-[10px]"
              >
                Cancel
              </Button>
              <Button type="submit" className="h-9 text-[10px]">
                Create Stream
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Fullscreen Overlay */}
      <AnimatePresence>
        {isFullscreen && selectedCam.status === "online" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-slate-950 flex flex-col justify-between p-4"
          >
            <div className="flex justify-between items-center text-white px-2 mb-2">
              <div>
                <strong className="text-sm block">{selectedCam.name} (FULLSCREEN MONITOR)</strong>
                <span className="text-[10px] text-slate-400">{selectedCam.location}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsFullscreen(false)}
                className="h-8 border-white/20 text-white hover:bg-white/10 text-[10px] font-bold"
              >
                <Minimize2 size={12} className="mr-1.5" /> Close Fullscreen
              </Button>
            </div>
            
            <div className="flex-1 flex items-center justify-center p-4">
              <canvas
                ref={isFullscreen ? canvasRef : null}
                className="w-full max-h-[85vh] rounded-2xl border border-slate-800 bg-slate-900 aspect-video"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header Panel */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">CCTV Command Room</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
            Manage RTSP networks, local webcams, and view live YOLO bounding boxes.
          </p>
        </div>

        <Button
          size="sm"
          onClick={() => setIsAddOpen(true)}
          className="text-[10px] font-bold h-9 bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-500/20"
        >
          <Plus size={12} className="mr-1" /> Add Camera Link
        </Button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        
        {/* Left Side: Filter and Checkpoint selection lists */}
        <div className="xl:col-span-1 space-y-6">
          <Card className="glass-card p-4 space-y-4">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <SlidersHorizontal size={14} className="text-blue-500" />
              Sensor Filters
            </CardTitle>
            
            <div className="relative">
              <Search size={14} className="absolute left-3 top-3 text-slate-400" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search camera or location..."
                className="pl-9 text-xs h-9"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-450 uppercase">Network Link Status</label>
              <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="h-9 text-xs">
                <option value="all">All Checkpoints</option>
                <option value="online">Online feeds</option>
                <option value="offline">Offline feeds</option>
              </Select>
            </div>
          </Card>

          {/* Camera checkpoints list */}
          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
            {filteredCams.map((cam) => {
              const isSelected = selectedCam.id === cam.id;
              return (
                <div
                  key={cam.id}
                  onClick={() => setSelectedCam(cam)}
                  className={`p-3.5 rounded-2xl border transition-all duration-150 flex flex-col justify-between gap-3 cursor-pointer ${
                    isSelected
                      ? "border-blue-500 bg-blue-600/10 shadow-lg shadow-blue-500/5"
                      : "border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950/60 hover:bg-slate-100/50 dark:hover:bg-slate-900/60"
                  }`}
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1">
                        {cam.stream_type === "webcam" ? (
                          <Tv size={12} className="text-indigo-400" />
                        ) : cam.stream_type === "rtsp" ? (
                          <Globe size={12} className="text-amber-400" />
                        ) : (
                          <CameraIcon size={12} className="text-blue-400" />
                        )}
                        <span className="text-[9px] font-bold text-slate-450 uppercase">{cam.id}</span>
                      </div>
                      <div className="flex items-center gap-1 text-[9px] font-bold">
                        <span className={`h-1.5 w-1.5 rounded-full ${cam.status === "online" ? "bg-emerald-500" : "bg-red-500"}`} />
                        <span className="uppercase text-slate-400">{cam.status}</span>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-extrabold text-xs truncate text-slate-800 dark:text-slate-100">{cam.name}</h3>
                      <span className="text-[9px] text-slate-500 dark:text-slate-400 font-semibold flex items-center gap-0.5 mt-0.5">
                        <MapPin size={9} />
                        {cam.location}
                      </span>
                    </div>
                  </div>

                  {/* Diagnostic details */}
                  <div className="grid grid-cols-3 gap-1 text-[8px] font-extrabold border-t border-slate-150/30 dark:border-slate-855/40 pt-2 text-slate-500">
                    <div>
                      <span className="block uppercase text-slate-400">Flow</span>
                      <span className="text-slate-800 dark:text-slate-200">{cam.vehicles_count}</span>
                    </div>
                    <div>
                      <span className="block uppercase text-slate-400">Incidents</span>
                      <span className={cam.violations_count > 0 ? "text-red-500" : "text-slate-850 dark:text-slate-200"}>
                        {cam.violations_count}
                      </span>
                    </div>
                    <div>
                      <span className="block uppercase text-slate-400">Health</span>
                      <span className={
                        cam.health === "good" ? "text-emerald-500" : cam.health === "warning" ? "text-amber-500" : "text-red-500"
                      }>
                        {cam.health.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side: Monitor canvas panel & logs */}
        <div className="xl:col-span-3 space-y-6">
          <Card className="glass-card p-4 overflow-hidden border-slate-200/50 dark:border-slate-800/50 shadow-lg">
            
            {/* Monitor Screen Frame */}
            <div className="relative">
              {selectedCam.status === "online" ? (
                <canvas
                  ref={isFullscreen ? null : canvasRef}
                  className="w-full aspect-video rounded-xl border border-slate-200 dark:border-slate-850 bg-slate-950"
                />
              ) : (
                <div className="w-full aspect-video rounded-xl bg-slate-950 border border-slate-900 flex flex-col items-center justify-center text-center p-6 gap-3">
                  <div className="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 border border-red-500/20 animate-pulse">
                    <VideoOff size={22} />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-xs">CCTV Stream Offline</h3>
                    <p className="text-[10px] text-slate-500 max-w-xs mt-1">
                      Signal timed out for sensor {selectedCam.id}. Verify IP port link credentials.
                    </p>
                  </div>
                </div>
              )}

              {/* Status Tags */}
              <div className="absolute top-4 right-4 flex gap-1.5 z-20">
                <Badge className="bg-black/60 border border-white/10 hover:bg-black/60 flex items-center gap-1.5 py-1 text-[9px] font-bold text-white">
                  <Radio size={10} className={`text-red-500 ${selectedCam.status === 'online' ? 'animate-ping' : ''}`} />
                  {selectedCam.status === "online" ? "LIVE INFRASTRUCTURE" : "CONNECTION LOST"}
                </Badge>
                
                {selectedCam.status === "online" && (
                  <Button
                    onClick={() => setIsFullscreen(true)}
                    variant="secondary"
                    className="bg-black/60 hover:bg-black/80 text-white border border-white/10 h-6 px-2 text-[9px] font-bold"
                  >
                    <Maximize2 size={10} className="mr-1" /> Fullscreen
                  </Button>
                )}
              </div>
            </div>

            {/* Viewport Control Panel */}
            <div className="flex flex-wrap items-center justify-between mt-3 pt-3 border-t border-slate-200/40 dark:border-slate-850/40 gap-4 text-xs font-bold">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <span className="text-slate-400">Check:</span>
                  <Badge variant={selectedCam.health === "good" ? "success" : selectedCam.health === "warning" ? "secondary" : "destructive"}>
                    {selectedCam.health.toUpperCase()}
                  </Badge>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 font-bold">Connection:</span>
                  <Button
                    variant={selectedCam.status === "online" ? "destructive" : "default"}
                    size="sm"
                    onClick={toggleCameraLink}
                    className="h-7 text-[9px] px-2.5 font-bold"
                  >
                    {selectedCam.status === "online" ? "Disconnect" : "Connect"}
                  </Button>
                </div>
              </div>

              {selectedCam.status === "online" && (
                <div className="flex items-center gap-2">
                  {selectedCam.stream_type === "simulated" && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowLanes(!showLanes)}
                      className="h-7 text-[9px] font-bold"
                    >
                      {showLanes ? "Hide Lanes" : "Lanes Overlay"}
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => alert(`Saved camera snapshot clip for node ${selectedCam.id}`)}
                    className="h-7 text-[9px] font-bold"
                  >
                    Snapshot
                  </Button>
                </div>
              )}
            </div>
          </Card>

          {/* CCTV Diagnostic logs */}
          <Card className="glass-card p-5 space-y-4">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-450 flex items-center gap-1.5">
              <Clock size={16} className="text-blue-500" />
              Live Telemetry Logs ({selectedCam.id})
            </CardTitle>
            <div className="h-32 overflow-y-auto font-mono text-[9px] leading-relaxed space-y-1.5 p-3 rounded-xl bg-slate-900/60 dark:bg-slate-950/60 border border-slate-300/10">
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

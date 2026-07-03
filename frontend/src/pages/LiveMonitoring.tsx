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
  Settings,
  EyeOff,
  Sun,
  Flame,
  CloudRain
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
  
  // Search Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  
  // Advanced AI toggles
  const [faceBlur, setFaceBlur] = useState(false);
  const [nightVision, setNightVision] = useState(false);
  const [roadDamageScanner, setRoadDamageScanner] = useState(false);
  const [weatherType, setWeatherType] = useState<"sunny" | "rainy" | "foggy">("sunny");
  
  // Real-time AI Target Spotter panel state
  const [spottedTarget, setSpottedTarget] = useState({
    vehicle: "Car",
    plate: "PB10AB1234",
    speed: 72,
    violation: "No Helmet",
    confidence: 98,
    time: "10:35:26"
  });
  
  // HUD Alerts triggered by AI loop
  const [isAccidentAlert, setIsAccidentAlert] = useState(false);
  const [isEmergencyAlert, setIsEmergencyAlert] = useState(false);
  const [isFireAlert, setIsFireAlert] = useState(false);
  const [isStolenAlert, setIsStolenAlert] = useState(false);
  const [alertPlate, setAlertPlate] = useState("");
  const [density, setDensity] = useState("Medium");
  
  // Counters
  const [counts, setCounts] = useState({ car: 2, motorcycle: 1, truck: 0, bus: 0, auto: 1 });

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
      
      const time = new Date().toTimeString().split(" ")[0]; // e.g. "10:35:26"
      const isReqDemo = Math.random() < 0.35;
      
      const type = isReqDemo ? "Car" : vTypes[Math.floor(Math.random() * vTypes.length)];
      const plate = isReqDemo ? "PB10AB1234" : plates[Math.floor(Math.random() * plates.length)];
      const speed = isReqDemo ? 72 : Math.floor(Math.random() * 45) + 35;
      const violation = isReqDemo ? "No Helmet" : (Math.random() < 0.25 ? "Wrong Lane Driving" : "None");
      const confidence = isReqDemo ? 98 : Math.floor(Math.random() * 8) + 91;

      // Sync Real-Time AI Target Spotter HUD panel
      setSpottedTarget({
        vehicle: type,
        plate: plate,
        speed: speed,
        violation: violation === "None" ? "No Violation" : violation,
        confidence: confidence,
        time: time
      });

      let logText = `${type} logged (Plate: ${plate}) | Speed: ${speed} km/h`;
      let isViolation = violation !== "None";

      if (isViolation) {
        logText = `⚠️ INCIDENT: ${violation} by ${type} (${plate}). Fine logged.`;
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
    let frameNumber = 0;

    // Simulated Bounding Boxes
    let vehicles = [
      { id: 1, x: 50, y: 150, speed: 2.8, type: "Car", plate: "DL 3C AB 9081", color: "#3b82f6", width: 62, height: 35, violating: false, isEmergency: false, isStolen: false },
      { id: 2, x: 300, y: 240, speed: 1.8, type: "Truck", plate: "MH 12 RN 4567", color: "#64748b", width: 88, height: 46, violating: false, isEmergency: false, isStolen: false },
      { id: 3, x: 550, y: 190, speed: 2.2, type: "Auto", plate: "KA 05 XY 5678", color: "#f59e0b", width: 48, height: 32, violating: false, isEmergency: false, isStolen: false }
    ];

    const drawLoop = () => {
      frameNumber++;
      
      // 1. Draw Stream Source
      if (selectedCam.stream_type === "webcam" && webcamVideoRef.current && webcamVideoRef.current.readyState >= 2) {
        ctx.drawImage(webcamVideoRef.current, 0, 0, canvas.width, canvas.height);
      } else {
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

      // --- Advanced Feature 1: Weather Rendering ---
      if (weatherType === "rainy") {
        ctx.strokeStyle = "rgba(174, 219, 255, 0.35)";
        ctx.lineWidth = 1.5;
        for (let i = 0; i < 20; i++) {
          const rx = (Math.random() * canvas.width + frameNumber * 3) % canvas.width;
          const ry = Math.random() * canvas.height;
          ctx.beginPath();
          ctx.moveTo(rx, ry);
          ctx.lineTo(rx - 5, ry + 15);
          ctx.stroke();
        }
      } else if (weatherType === "foggy") {
        ctx.fillStyle = "rgba(255, 255, 255, 0.12)";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }

      // --- Advanced Feature 2: Road Damage Scanner ---
      if (roadDamageScanner && selectedCam.stream_type === "simulated") {
        ctx.strokeStyle = "#eab308";
        ctx.lineWidth = 2.5;
        // Draw simulated potholes on lanes
        ctx.beginPath();
        ctx.arc(220, 210, 14, 0, Math.PI * 2);
        ctx.arc(480, 310, 18, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = "rgba(234, 179, 8, 0.2)";
        ctx.fill();
        ctx.fillStyle = "#eab308";
        ctx.font = "bold 9px monospace";
        ctx.fillText("STRUCTURAL HOLE [CRITICAL]", 240, 215);
      }

      // Signal Simulator
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

      // Trigger simulated accidents, stolen warnings, and emergency vehicles randomly
      if (frameNumber % 400 === 0 && selectedCam.stream_type === "simulated") {
        const triggers = [
          () => { setIsAccidentAlert(true); setTimeout(() => setIsAccidentAlert(false), 5000); },
          () => { setIsEmergencyAlert(true); setTimeout(() => setIsEmergencyAlert(false), 5000); },
          () => { setIsFireAlert(true); setTimeout(() => setIsFireAlert(false), 5000); },
          () => { setIsStolenAlert(true); setAlertPlate(vehicles[0].plate); setTimeout(() => setIsStolenAlert(false), 5000); }
        ];
        triggers[Math.floor(Math.random() * triggers.length)]();
      }

      // Draw Bounding Boxes
      if (selectedCam.stream_type === "webcam") {
        const frameTime = performance.now();
        const cycle = Math.sin(frameTime / 2000) * 120;
        
        ctx.strokeStyle = "#22c55e";
        ctx.lineWidth = 2.5;
        ctx.strokeRect(200 + cycle, 120, 180, 210);
        ctx.fillStyle = "#22c55e";
        ctx.font = "bold 11px monospace";
        ctx.fillText("Person [Conf: 0.94] (0 km/h)", 200 + cycle, 112);

        // Pedestrian Face Blur Privacy Mode
        if (faceBlur) {
          ctx.fillStyle = "rgba(100, 100, 100, 0.98)";
          ctx.beginPath();
          ctx.arc(290 + cycle, 165, 24, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = "#ffffff";
          ctx.font = "bold 8px monospace";
          ctx.fillText("PRIVACY BLUR", 260 + cycle, 168);
        }

        ctx.strokeStyle = "#eab308";
        ctx.strokeRect(250 + cycle, 280, 80, 25);
      } else {
        // Density calculation
        setDensity(vehicles.length >= 3 ? "High" : vehicles.length >= 1 ? "Medium" : "Low");
        
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

          // Bounding Box color
          let boxColor = v.violating ? "#ef4444" : "#10b981";
          
          if (isStolenAlert && v.id === 1) {
            boxColor = "#a855f7"; // purple stolen pin
            v.isStolen = true;
          }
          if (isEmergencyAlert && v.id === 3) {
            boxColor = "#3b82f6"; // blue emergency pin
            v.isEmergency = true;
          }

          ctx.strokeStyle = boxColor;
          ctx.lineWidth = 2.5;
          ctx.strokeRect(v.x, v.y, v.width, v.height);

          // Trace line path vector (demonstrates multi-frame tracking history)
          ctx.strokeStyle = `${boxColor}55`; // opacity
          ctx.lineWidth = 1.5;
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.moveTo(v.x, v.y + v.height / 2);
          ctx.lineTo(Math.max(10, v.x - 80), v.y + v.height / 2);
          ctx.stroke();
          ctx.setLineDash([]); // Reset line dash

          // Face blur on driver cockpit if active
          if (faceBlur) {
            ctx.fillStyle = "rgba(50,50,50,0.98)";
            ctx.beginPath();
            ctx.arc(v.x + v.width * 0.3, v.y + v.height * 0.4, 8, 0, Math.PI * 2);
            ctx.fill();
          }

          // Label - Multi-frame persistent Tracking ID
          ctx.fillStyle = boxColor;
          ctx.font = "bold 9.5px monospace";
          const trackingTag = `Vehicle #00${v.id}`;
          const classTag = v.isStolen ? "STOLEN!" : v.isEmergency ? "EMERGENCY" : v.type.toUpperCase();
          ctx.fillText(`${trackingTag} | ${classTag} (${Math.round(v.speed * 25)} km/h)`, v.x, v.y - 7);

        });
      }

      // Calculate real-time FPS
      const now = performance.now();
      frameCountRef.current++;
      
      if (now - lastFpsUpdateTimeRef.current >= 1000) {
        const calculatedFps = Math.round((frameCountRef.current * 1000) / (now - lastFpsUpdateTimeRef.current));
        setFps(calculatedFps);
        frameCountRef.current = 0;
        lastFpsUpdateTimeRef.current = now;
      }
      
      // HUD Overlay details - Live AI Telemetry counters
      ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
      ctx.fillRect(15, 15, 230, 110);
      ctx.strokeStyle = "rgba(59, 130, 246, 0.3)";
      ctx.strokeRect(15, 15, 230, 110);

      ctx.fillStyle = "#60a5fa";
      ctx.font = "bold 10px monospace";
      ctx.fillText(`CAM NODE: ${selectedCam.id}`, 25, 30);
      ctx.fillText(`MODE: ${selectedCam.stream_type.toUpperCase()}`, 25, 45);
      ctx.fillText(`WEATHER: ${weatherType.toUpperCase()}`, 25, 60);
      
      // Live AI System metrics
      const activeFps = selectedCam.status === "online" ? 31 : 0;
      const activeLatency = selectedCam.status === "online" ? 18 : 0;
      const activeInference = selectedCam.status === "online" ? 25 : 0;

      ctx.fillStyle = "#34d399";
      ctx.fillText(`FPS: ${activeFps} FPS`, 25, 75);
      ctx.fillText(`LATENCY: ${activeLatency} ms`, 25, 90);
      ctx.fillText(`INFERENCE: ${activeInference} ms`, 25, 105);

      // Warning Alerts Overlay Banners on Canvas
      if (isAccidentAlert) {
        ctx.fillStyle = "rgba(239, 68, 68, 0.9)";
        ctx.fillRect(15, canvas.height - 45, canvas.width - 30, 30);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px monospace";
        ctx.fillText("⚠️ CRITICAL ALARM: ACCIDENT SCENARIO DETECTED! HIGH HAZARD RADAR ALERT ACTIVE.", 30, canvas.height - 25);
      } else if (isEmergencyAlert) {
        ctx.fillStyle = "rgba(59, 130, 246, 0.9)";
        ctx.fillRect(15, canvas.height - 45, canvas.width - 30, 30);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px monospace";
        ctx.fillText("🚨 DISPATCH ALARM: EMERGENCY PRIORITY VEHICLE DETECTED. LANE CLEARING DISPATCH ACTIVE.", 30, canvas.height - 25);
      } else if (isFireAlert) {
        ctx.fillStyle = "rgba(249, 115, 22, 0.9)";
        ctx.fillRect(15, canvas.height - 45, canvas.width - 30, 30);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px monospace";
        ctx.fillText("🔥 FIRE HAZARD WARNING: THERMAL SMOKE/FIRE SPIKE DETECTED. ALARM SENT.", 30, canvas.height - 25);
      } else if (isStolenAlert) {
        ctx.fillStyle = "rgba(168, 85, 247, 0.9)";
        ctx.fillRect(15, canvas.height - 45, canvas.width - 30, 30);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px monospace";
        ctx.fillText(`🚨 STOLEN VEHICLE DETECTED (PLATE: ${alertPlate})! DISPATCHING CRUISERS.`, 30, canvas.height - 25);
      }

      animationRef.current = requestAnimationFrame(drawLoop);
    };

    drawLoop();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [selectedCam.id, selectedCam.status, selectedCam.stream_type, showLanes, fps, faceBlur, roadDamageScanner, weatherType, isAccidentAlert, isEmergencyAlert, isFireAlert, isStolenAlert]);

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

    setNewCamName("");
    setNewCamLoc("");
    setNewCamType("simulated");
    setNewCamIp("");
    setNewCamRtsp("");
  };

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
            Manage RTSP networks, local webcams, and run advanced AI target models.
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
                        <span className="text-[9px] font-bold text-slate-455 uppercase">{cam.id}</span>
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
                </div>
              );
            })}
          </div>
        </div>

        {/* Center/Right Side: Monitor canvas panel & logs */}
        <div className="xl:col-span-3 space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Monitor Screen Frame */}
            <div className="lg:col-span-2 space-y-4">
              <Card className="glass-card p-4 overflow-hidden border-slate-200/50 dark:border-slate-800/50 shadow-lg">
                
                <div className="relative">
                  {selectedCam.status === "online" ? (
                    <canvas
                      ref={isFullscreen ? null : canvasRef}
                      className="w-full aspect-video rounded-xl border border-slate-200 dark:border-slate-850 bg-slate-950 transition-all duration-300"
                      style={nightVision ? { filter: "hue-rotate(90deg) brightness(1.2) contrast(1.5) saturate(1.2)" } : {}}
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
                      <span className="text-slate-400">Status:</span>
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

            {/* Right Side: Advanced AI Tuning Controls */}
            <div className="space-y-6">
              <Card className="glass-card p-5 space-y-4">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <SlidersHorizontal size={14} className="text-blue-500" />
                  Advanced AI Scanner Tools
                </CardTitle>

                <div className="space-y-3.5 text-xs font-semibold">
                  
                  {/* Face Blur Toggle */}
                  <div className="flex items-center justify-between border-b border-slate-200/40 dark:border-slate-850/40 pb-2.5">
                    <div>
                      <span className="block font-bold">Face Blur Anonymize</span>
                      <span className="text-[8px] text-slate-400">Blur pedestrian cockpit faces</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={faceBlur}
                      onChange={() => setFaceBlur(!faceBlur)}
                      className="rounded bg-slate-950 border-slate-700 h-4 w-4 accent-blue-500 cursor-pointer"
                    />
                  </div>

                  {/* Night Vision Toggle */}
                  <div className="flex items-center justify-between border-b border-slate-200/40 dark:border-slate-850/40 pb-2.5">
                    <div>
                      <span className="block font-bold">Night Vision Mode</span>
                      <span className="text-[8px] text-slate-400">Activate thermal lens overlay</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={nightVision}
                      onChange={() => setNightVision(!nightVision)}
                      className="rounded bg-slate-950 border-slate-700 h-4 w-4 accent-blue-500 cursor-pointer"
                    />
                  </div>

                  {/* Road Damage Toggle */}
                  <div className="flex items-center justify-between border-b border-slate-200/40 dark:border-slate-850/40 pb-2.5">
                    <div>
                      <span className="block font-bold">Road Damage Scanner</span>
                      <span className="text-[8px] text-slate-400">Trak cracks / potholes</span>
                    </div>
                    <input
                      type="checkbox"
                      checked={roadDamageScanner}
                      onChange={() => setRoadDamageScanner(!roadDamageScanner)}
                      className="rounded bg-slate-950 border-slate-700 h-4 w-4 accent-blue-500 cursor-pointer"
                    />
                  </div>

                  {/* Weather Sensor Dropdown */}
                  <div className="space-y-1 border-b border-slate-200/40 dark:border-slate-850/40 pb-3">
                    <label className="text-[8px] font-bold text-slate-400 uppercase block">Weather Sensor Matrix</label>
                    <Select
                      value={weatherType}
                      onChange={(e: any) => setWeatherType(e.target.value)}
                      className="h-8 text-[10px]"
                    >
                      <option value="sunny">Sunny (Clear Sky)</option>
                      <option value="rainy">Rainy (Precipitation)</option>
                      <option value="foggy">Foggy (Mist/Smog)</option>
                    </Select>
                  </div>

                  {/* Density badge status */}
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-400">Traffic Density</span>
                    <Badge variant={density === 'High' ? 'destructive' : 'success'}>
                      {density}
                    </Badge>
                  </div>

                </div>
              </Card>

              {/* Real-Time AI Target Spotter Panel */}
              <Card className="glass-card p-5 space-y-4 border-blue-500/20 shadow-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-xl pointer-events-none"></div>
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Activity size={15} className="text-blue-500 animate-pulse" />
                    AI Target Spotter
                  </span>
                  <Badge variant="outline" className="text-[8px] border-blue-500/30 text-blue-500 font-bold py-0.5 animate-pulse">
                    ACTIVE MODEL
                  </Badge>
                </CardTitle>
                
                <div className="space-y-2.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
                  <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-2">
                    <span className="text-slate-450 uppercase text-[9px] font-bold">Vehicle Class</span>
                    <strong className="text-slate-800 dark:text-slate-100 flex items-center gap-1">
                      <Car size={13} className="text-blue-400" />
                      {spottedTarget.vehicle}
                    </strong>
                  </div>
                  
                  <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-2">
                    <span className="text-slate-455 uppercase text-[9px] font-bold">Licence Plate</span>
                    <Badge className="bg-slate-900 border border-slate-750 text-white font-mono text-[10.5px] px-2 py-0.5 tracking-wider">
                      {spottedTarget.plate}
                    </Badge>
                  </div>
                  
                  <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-2">
                    <span className="text-slate-455 uppercase text-[9px] font-bold">Target Speed</span>
                    <strong className={`text-xs ${spottedTarget.speed > 60 ? 'text-red-500 font-extrabold animate-pulse' : 'text-slate-800 dark:text-slate-100'}`}>
                      {spottedTarget.speed} km/h
                    </strong>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-2">
                    <span className="text-slate-455 uppercase text-[9px] font-bold">Infraction Type</span>
                    <Badge variant={spottedTarget.violation === 'No Helmet' || spottedTarget.violation === 'Wrong Lane Driving' ? 'destructive' : 'secondary'} className="text-[9.5px] font-bold py-0.5">
                      {spottedTarget.violation}
                    </Badge>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-2">
                    <span className="text-slate-455 uppercase text-[9px] font-bold">Model Confidence</span>
                    <strong className="text-emerald-500 font-extrabold">{spottedTarget.confidence}%</strong>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-slate-455 uppercase text-[9px] font-bold">Capture Time</span>
                    <span className="text-slate-500 dark:text-slate-400 font-mono text-[10px]">{spottedTarget.time}</span>
                  </div>
                </div>
              </Card>

              {/* System Health Matrix Panel */}
              <Card className="glass-card p-5 space-y-4 border-emerald-500/20 shadow-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl pointer-events-none"></div>
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck size={15} className="text-emerald-500" />
                    Core Pipeline Status
                  </span>
                  <Badge variant="outline" className="text-[8px] border-emerald-500/30 text-emerald-505 font-bold py-0.5 animate-pulse text-emerald-400">
                    ALL SYSTEMS NOMINAL
                  </Badge>
                </CardTitle>
                
                <div className="space-y-2.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
                  <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-2">
                    <span className="text-slate-450 uppercase text-[9px] font-bold">YOLOv8 Engine</span>
                    <span className="flex items-center gap-1.5 text-emerald-500 font-bold text-[10px]">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                      Running
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-2">
                    <span className="text-slate-450 uppercase text-[9px] font-bold">EasyOCR Reader</span>
                    <span className="flex items-center gap-1.5 text-emerald-500 font-bold text-[10px]">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                      Running
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-2">
                    <span className="text-slate-450 uppercase text-[9px] font-bold">Camera Connection</span>
                    <span className={`flex items-center gap-1.5 font-bold text-[10px] ${selectedCam.status === 'online' ? 'text-emerald-500' : 'text-red-500'}`}>
                      <span className={`h-1.5 w-1.5 rounded-full animate-ping ${selectedCam.status === 'online' ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                      {selectedCam.status === 'online' ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>

                  <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-2">
                    <span className="text-slate-455 uppercase text-[9px] font-bold">SQL Database</span>
                    <span className="flex items-center gap-1.5 text-emerald-500 font-bold text-[10px]">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                      Connected
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-slate-455 uppercase text-[9px] font-bold">FastAPI Gateway</span>
                    <span className="flex items-center gap-1.5 text-emerald-500 font-bold text-[10px]">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                      Healthy
                    </span>
                  </div>
                </div>
              </Card>

              {/* AI Confidence Gauge Card */}
              <Card className="glass-card p-5 space-y-4 border-blue-500/10 shadow-lg relative overflow-hidden flex flex-col items-center">
                <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full blur-xl pointer-events-none"></div>
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 w-full justify-start">
                  <Activity size={15} className="text-blue-500 animate-pulse" />
                  AI Confidence Gauge
                </CardTitle>
                
                <div className="relative flex items-center justify-center my-2">
                  <svg className="w-28 h-28 transform -rotate-90">
                    <circle
                      cx="56"
                      cy="56"
                      r="46"
                      className="stroke-slate-200 dark:stroke-slate-800"
                      strokeWidth="8"
                      fill="transparent"
                    />
                    <circle
                      cx="56"
                      cy="56"
                      r="46"
                      className="stroke-blue-500"
                      strokeWidth="8"
                      fill="transparent"
                      strokeDasharray="289"
                      strokeDashoffset={289 - (289 * 98) / 100}
                      strokeLinecap="round"
                      style={{ transition: "stroke-dashoffset 1s ease-in-out" }}
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="text-2xl font-extrabold tracking-tight text-slate-800 dark:text-slate-100">98%</span>
                    <span className="text-[7.5px] text-slate-400 font-bold uppercase tracking-widest">Confidence</span>
                  </div>
                </div>

                <div className="text-[9.5px] text-slate-400 font-semibold text-center mt-1 w-full bg-slate-900/40 p-2 rounded-xl border border-white/5">
                  🛡️ Active YOLOv8 Model: High Reliability State
                </div>
              </Card>

              {/* Class Vehicle Counting Card */}
              <Card className="glass-card p-5 space-y-3">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Car size={15} className="text-blue-500" />
                  Vehicle Classification Counts
                </CardTitle>

                <div className="grid grid-cols-2 gap-3 text-xs font-semibold">
                  <div className="p-2.5 rounded-xl border border-slate-200/40 dark:border-slate-800/40 text-center">
                    <span className="text-[8.5px] text-slate-400 block font-bold uppercase">Cars</span>
                    <strong className="text-sm">{counts.car}</strong>
                  </div>
                  <div className="p-2.5 rounded-xl border border-slate-200/40 dark:border-slate-800/40 text-center">
                    <span className="text-[8.5px] text-slate-400 block font-bold uppercase">Motorcycles</span>
                    <strong className="text-sm">{counts.motorcycle}</strong>
                  </div>
                  <div className="p-2.5 rounded-xl border border-slate-200/40 dark:border-slate-800/40 text-center">
                    <span className="text-[8.5px] text-slate-400 block font-bold uppercase">Trucks/Buses</span>
                    <strong className="text-sm">{counts.truck + counts.bus}</strong>
                  </div>
                  <div className="p-2.5 rounded-xl border border-slate-200/40 dark:border-slate-800/40 text-center">
                    <span className="text-[8.5px] text-slate-400 block font-bold uppercase">Auto Rickshaws</span>
                    <strong className="text-sm">{counts.auto}</strong>
                  </div>
                </div>
              </Card>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}

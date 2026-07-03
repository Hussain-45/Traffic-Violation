import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog";
import { motion, AnimatePresence } from "framer-motion";
import {
  MapPin,
  Info,
  Layers,
  Camera,
  AlertTriangle,
  Flame,
  Globe,
  Settings,
  X,
  Eye,
  CheckCircle
} from "lucide-react";

interface MapCamera {
  id: string
  name: string
  lat: number
  lng: number
  status: "online" | "offline"
}

interface MapViolation {
  id: number
  plate: string
  type: string
  lat: number
  lng: number
  speed: number
  fine: number
  time: string
  location: string
  status: "pending" | "paid" | "resolved"
}

interface MapCluster {
  id: string
  name: string
  lat: number
  lng: number
  camera_count: number
  violation_count: number
}

// Coordinate seeding data (mapped to Delhi NCR region coordinates bounds)
const mockCameras: MapCamera[] = [
  { id: "CAM-001", name: "Connaught Place Outer Ring", lat: 28.6304, lng: 77.2177, status: "online" },
  { id: "CAM-002", name: "India Gate Circle", lat: 28.6129, lng: 77.2295, status: "online" },
  { id: "CAM-003", name: "Rajouri Garden Flyover", lat: 28.6415, lng: 77.1245, status: "online" },
  { id: "CAM-004", name: "AIIMS Crossing Main Feed", lat: 28.5672, lng: 77.2100, status: "offline" },
  { id: "CAM-005", name: "Karol Bagh Bazar Market", lat: 28.6441, lng: 77.1895, status: "online" }
];

const mockViolations: MapViolation[] = [
  { id: 201, plate: "DL 3C AW 9081", type: "Red Light Jump", lat: 28.6310, lng: 77.2185, speed: 45, fine: 2000, time: "10:18 AM", location: "Connaught Place Sector 1", status: "pending" },
  { id: 202, plate: "MH 12 RN 4567", type: "Overspeeding", lat: 28.6135, lng: 77.2301, speed: 82, fine: 1000, time: "09:42 AM", location: "India Gate Circular 3", status: "paid" },
  { id: 203, plate: "KA 05 XY 5678", type: "No Helmet", lat: 28.6420, lng: 77.1250, speed: 38, fine: 500, time: "09:05 AM", location: "Rajouri Garden Flyover", status: "pending" },
  { id: 204, plate: "HR 26 AZ 1212", type: "Wrong Lane Driving", lat: 28.5680, lng: 77.2105, speed: 52, fine: 1000, time: "08:15 AM", location: "AIIMS Crossing", status: "resolved" },
  { id: 205, plate: "UP 16 PQ 8890", type: "Triple Riding", lat: 28.6445, lng: 77.1901, speed: 29, fine: 1000, time: "07:30 AM", location: "Karol Bagh Bazar", status: "pending" },
  { id: 206, plate: "DL 3C MX 9821", type: "Overspeeding", lat: 28.6300, lng: 77.2165, speed: 76, fine: 1000, time: "11:05 AM", location: "Connaught Place Sector 3", status: "pending" }
];

const mockClusters: MapCluster[] = [
  { id: "CL-01", name: "Central Hub Cluster", lat: 28.6250, lng: 77.2200, camera_count: 2, violation_count: 35 },
  { id: "CL-02", name: "West Ring Cluster", lat: 28.6425, lng: 77.1400, camera_count: 1, violation_count: 15 },
  { id: "CL-03", name: "South Interchange Cluster", lat: 28.5700, lng: 77.2100, camera_count: 2, violation_count: 42 }
];

export default function InteractiveMap() {
  const { token } = useContext(AuthContext);

  // Layer switches
  const [showCameras, setShowCameras] = useState(true);
  const [showViolations, setShowViolations] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showDangerZones, setShowDangerZones] = useState(true);
  const [showClusters, setShowClusters] = useState(false);

  // Click selections
  const [selectedCam, setSelectedCam] = useState<MapCamera | null>(null);
  const [selectedViol, setSelectedViol] = useState<MapViolation | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<MapCluster | null>(null);

  const mapWidth = 800;
  const mapHeight = 450;

  // Projection formula translating GPS Lat/Lng to local SVG pixel space
  const getXY = (lat: number, lng: number) => {
    const minLat = 28.55;
    const maxLat = 28.66;
    const minLng = 77.10;
    const maxLng = 77.25;

    const x = ((lng - minLng) / (maxLng - minLng)) * mapWidth;
    const y = mapHeight - ((lat - minLat) / (maxLat - minLat)) * mapHeight;

    return { x: Math.round(x), y: Math.round(y) };
  };

  return (
    <div className="space-y-6">
      
      {/* Violation Pin Details Modal */}
      <Dialog open={selectedViol !== null} onOpenChange={() => setSelectedViol(null)}>
        <DialogContent className="glass-card text-slate-100 max-w-sm border-slate-800 p-6">
          {selectedViol && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                  <AlertTriangle className="text-red-500 shrink-0" size={20} />
                  <div>
                    <DialogTitle className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Violation Incident #{selectedViol.id}
                    </DialogTitle>
                    <DialogDescription className="text-[9px] text-slate-500 font-semibold">
                      Automated AI infraction capture details.
                    </DialogDescription>
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-3.5 my-3 text-xs font-semibold">
                <div className="flex justify-between items-center">
                  <span className="text-slate-450">Offence Type</span>
                  <Badge variant="destructive" className="text-[8px] py-0 px-2 font-extrabold uppercase">
                    {selectedViol.type}
                  </Badge>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-slate-455">License Plate</span>
                  <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-none font-bold text-[9px] py-0 px-2">
                    {selectedViol.plate}
                  </Badge>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-455">Recorded Speed</span>
                  <span className="text-slate-200">{selectedViol.speed} km/h</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-455">Fine Tariff</span>
                  <span className="text-slate-100 font-bold">₹{selectedViol.fine.toLocaleString()}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-455">Timestamp</span>
                  <span className="text-slate-400 font-mono">{selectedViol.time}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-slate-455">Location Grid</span>
                  <span className="text-slate-400 truncate max-w-[150px]">{selectedViol.location}</span>
                </div>
              </div>

              <DialogFooter className="pt-2">
                <Button
                  onClick={() => setSelectedViol(null)}
                  size="sm"
                  className="w-full text-[10px] font-bold h-8"
                >
                  Close Audit Sheet
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Interactive GIS Map</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
          Spatial analysis grids depicting online cameras, threat zones, and cluster groups.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        
        {/* SVG Interactive Canvas */}
        <div className="xl:col-span-3">
          <Card className="glass-card p-4 shadow-lg overflow-hidden bg-slate-950 border-slate-200/50 dark:border-slate-800/50 relative">
            
            {/* Layers overlay selector bar */}
            <div className="absolute top-8 left-8 p-3 rounded-2xl bg-black/75 border border-white/10 backdrop-blur z-20 space-y-2.5 text-[9px] font-bold text-slate-300 print:hidden">
              <span className="text-slate-500 uppercase tracking-widest block border-b border-white/5 pb-1">Map Layers</span>
              
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={showCameras} onChange={() => setShowCameras(!showCameras)} className="rounded bg-slate-900 border-slate-700" />
                <span className="text-blue-500">CCTV Nodes (Blue)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={showViolations} onChange={() => setShowViolations(!showViolations)} className="rounded bg-slate-900 border-slate-700" />
                <span className="text-red-500">Violations (Red)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={showHeatmap} onChange={() => setShowHeatmap(!showHeatmap)} className="rounded bg-slate-900 border-slate-700" />
                <span className="text-yellow-500">Heat Range</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={showDangerZones} onChange={() => setShowDangerZones(!showDangerZones)} className="rounded bg-slate-900 border-slate-700" />
                <span className="text-orange-500">Danger Sectors</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={showClusters} onChange={() => setShowClusters(!showClusters)} className="rounded bg-slate-900 border-slate-700" />
                <span className="text-indigo-400">Node Clusters</span>
              </label>
            </div>

            <div className="relative aspect-video w-full rounded-xl border border-slate-900 bg-slate-950 overflow-hidden">
              
              {/* Background grid markings */}
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:25px_25px] opacity-15" />
              
              <svg viewBox={`0 0 ${mapWidth} ${mapHeight}`} className="w-full h-full relative z-10 select-none">
                
                {/* Simulated Delhi road network lines */}
                <path d="M 50,120 Q 300,60 700,100 T 780,410" fill="none" stroke="rgba(71,85,105,0.25)" strokeWidth="6" />
                <path d="M 180,30 Q 220,240 310,430" fill="none" stroke="rgba(71,85,105,0.2)" strokeWidth="4" />
                <path d="M 40,300 L 760,280" fill="none" stroke="rgba(71,85,105,0.18)" strokeWidth="5" />
                <path d="M 400,20 Q 450,220 500,430" fill="none" stroke="rgba(71,85,105,0.15)" strokeWidth="3" />

                {/* 1. Heatmap overlay nodes (Yellow semitransparent halos) */}
                {showHeatmap && mockViolations.map((viol, idx) => {
                  const { x, y } = getXY(viol.lat, viol.lng);
                  return (
                    <circle
                      key={`heat-${idx}`}
                      cx={x}
                      cy={y}
                      r="32"
                      fill="rgba(245,158,11,0.08)"
                      stroke="rgba(245,158,11,0.15)"
                      strokeWidth="1"
                    />
                  );
                })}

                {/* 2. Danger Zones (Red shaded zones for High Incident regions like AIIMS and Connaught Place) */}
                {showDangerZones && (
                  <>
                    {/* CP Area */}
                    <circle cx="640" cy="120" r="55" fill="rgba(239,68,68,0.05)" stroke="rgba(239,68,68,0.2)" strokeWidth="1.5" strokeDasharray="3 3" />
                    {/* AIIMS Area */}
                    <circle cx="600" cy="380" r="48" fill="rgba(239,68,68,0.05)" stroke="rgba(239,68,68,0.2)" strokeWidth="1.5" strokeDasharray="3 3" />
                  </>
                )}

                {/* 3. CCTV Camera Markers (Blue pins) */}
                {showCameras && mockCameras.map((cam) => {
                  const { x, y } = getXY(cam.lat, cam.lng);
                  const isSelected = selectedCam?.id === cam.id;
                  
                  return (
                    <g
                      key={cam.id}
                      onClick={() => {
                        setSelectedCam(cam);
                        setSelectedViol(null);
                        setSelectedCluster(null);
                      }}
                      className="cursor-pointer group"
                    >
                      <circle
                        cx={x}
                        cy={y}
                        r="12"
                        fill="rgba(59,130,246,0.15)"
                        className="group-hover:scale-120 transition-transform origin-center"
                      />
                      <circle
                        cx={x}
                        cy={y}
                        r={isSelected ? "7" : "5"}
                        fill={cam.status === "online" ? "#3b82f6" : "#64748b"}
                        stroke="#ffffff"
                        strokeWidth="1.5"
                      />
                    </g>
                  );
                })}

                {/* 4. Violation Markers (Red pins - Click opens Audit Modal) */}
                {showViolations && mockViolations.map((viol) => {
                  const { x, y } = getXY(viol.lat, viol.lng);
                  return (
                    <g
                      key={viol.id}
                      onClick={() => {
                        setSelectedViol(viol);
                        setSelectedCam(null);
                        setSelectedCluster(null);
                      }}
                      className="cursor-pointer group"
                    >
                      <circle
                        cx={x}
                        cy={y}
                        r="10"
                        fill="rgba(239,68,68,0.2)"
                        className="group-hover:scale-120 transition-transform origin-center"
                      />
                      <circle
                        cx={x}
                        cy={y}
                        r="4"
                        fill="#ef4444"
                        stroke="#ffffff"
                        strokeWidth="1"
                      />
                    </g>
                  );
                })}

                {/* 5. Cluster Markers (Group count bubbles) */}
                {showClusters && mockClusters.map((cluster) => {
                  const { x, y } = getXY(cluster.lat, cluster.lng);
                  const isSelected = selectedCluster?.id === cluster.id;
                  
                  return (
                    <g
                      key={cluster.id}
                      onClick={() => {
                        setSelectedCluster(cluster);
                        setSelectedCam(null);
                        setSelectedViol(null);
                      }}
                      className="cursor-pointer group"
                    >
                      <circle
                        cx={x}
                        cy={y}
                        r="20"
                        fill="rgba(139,92,246,0.22)"
                        stroke="rgba(139,92,246,0.4)"
                        strokeWidth="2"
                        className="group-hover:scale-110 transition-transform origin-center"
                      />
                      <text
                        x={x}
                        y={y + 3}
                        fill="#ffffff"
                        fontSize="8px"
                        fontWeight="extrabold"
                        textAnchor="middle"
                      >
                        {cluster.violation_count}
                      </text>
                    </g>
                  );
                })}

              </svg>

              <div className="absolute bottom-4 left-4 p-2.5 bg-black/75 rounded-xl border border-white/10 text-[9px] font-bold text-slate-400 backdrop-blur z-20 flex flex-col gap-1.5 print:hidden">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-blue-500"></span> CCTV Nodes
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-red-500"></span> Violation Markers
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-orange-550 border border-orange-500 border-dashed"></span> Danger Zones
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Dynamic Map sidebar information drawer */}
        <div>
          <AnimatePresence mode="wait">
            
            {/* Camera Details */}
            {selectedCam && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                key="cam-info"
              >
                <Card className="glass-card p-5 space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-200/40 dark:border-slate-800/40 pb-3">
                    <Camera size={16} className="text-blue-500" />
                    <div className="min-w-0">
                      <h3 className="font-extrabold text-xs truncate max-w-[130px]">{selectedCam.name}</h3>
                      <span className="text-[8px] text-slate-450 font-bold uppercase block">CCTV Node Status</span>
                    </div>
                  </div>

                  <div className="space-y-2.5 text-xs font-semibold">
                    <div className="flex justify-between">
                      <span className="text-slate-455">Camera ID</span>
                      <span className="text-slate-700 dark:text-slate-300 font-bold">{selectedCam.id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-455">Connection</span>
                      <Badge variant={selectedCam.status === 'online' ? 'success' : 'secondary'}>
                        {selectedCam.status.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-455">Coordinates</span>
                      <span className="text-slate-400 font-mono">{selectedCam.lat.toFixed(4)}°N</span>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Cluster Details */}
            {selectedCluster && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                key="cluster-info"
              >
                <Card className="glass-card p-5 space-y-4">
                  <div className="flex items-center gap-2 border-b border-slate-200/40 dark:border-slate-800/40 pb-3">
                    <Layers size={16} className="text-indigo-400" />
                    <div className="min-w-0">
                      <h3 className="font-extrabold text-xs truncate max-w-[130px]">{selectedCluster.name}</h3>
                      <span className="text-[8px] text-slate-450 font-bold uppercase block">Junction Cluster</span>
                    </div>
                  </div>

                  <div className="space-y-2.5 text-xs font-semibold">
                    <div className="flex justify-between">
                      <span className="text-slate-455">Checkpoints</span>
                      <span className="text-slate-700 dark:text-slate-350">{selectedCluster.camera_count} Cameras</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-455">Total Incidents</span>
                      <strong className="text-red-500 font-extrabold">{selectedCluster.violation_count} cases</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-455">Threat Tier</span>
                      <Badge variant="destructive">HIGH DENSITY</Badge>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}

            {/* No selection default state */}
            {!selectedCam && !selectedViol && !selectedCluster && (
              <Card className="glass-card p-5 text-center py-12 text-xs text-slate-400 font-bold flex flex-col items-center justify-center gap-2">
                <Globe className="text-slate-600 animate-spin" size={24} style={{ animationDuration: '6s' }} />
                <span>Select a node, violation pin, or cluster marker on the GIS map view.</span>
              </Card>
            )}

          </AnimatePresence>
        </div>

      </div>
    </div>
  );
}

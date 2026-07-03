import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { MapPin, Info } from "lucide-react";

interface HeatmapItem {
  lat: number
  lng: number
  name: string
  count: number
}

// Fallback mock hotspots map coordinates
const fallbackHeatmap: HeatmapItem[] = [
  { name: "Connaught Place Sector 3", lat: 28.6304, lng: 77.2177, count: 42 },
  { name: "India Gate Ring Circular", lat: 28.6129, lng: 77.2295, count: 28 },
  { name: "Rajouri Garden Flyover Intersection", lat: 28.6415, lng: 77.1245, count: 18 },
  { name: "AIIMS Traffic Crossings", lat: 28.5672, lng: 77.2100, count: 35 },
  { name: "Karol Bagh Market checkpoint 4", lat: 28.6441, lng: 77.1895, count: 12 }
];

export default function Map() {
  const { token } = useContext(AuthContext);
  const [heatmap, setHeatmap] = useState<HeatmapItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedPin, setSelectedPin] = useState<HeatmapItem | null>(null);

  useEffect(() => {
    const fetchHeatmap = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setHeatmap(data.heatmap);
          if (data.heatmap.length > 0) setSelectedPin(data.heatmap[0]);
        } else {
          throw new Error("API Offline");
        }
      } catch (err) {
        console.warn("Using offline mock hotspots coordinate dataset.");
        setHeatmap(fallbackHeatmap);
        setSelectedPin(fallbackHeatmap[0]);
      } finally {
        setLoading(false);
      }
    };
    fetchHeatmap();
  }, [token]);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 w-48 rounded bg-slate-200 dark:bg-slate-800"></div>
        <div className="h-96 rounded-2xl bg-slate-200 dark:bg-slate-800"></div>
      </div>
    );
  }

  const mapWidth = 800;
  const mapHeight = 450;

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
      <div>
        <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Geo Heatmap Command</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Geographical tracking of traffic checkpoints, violation density, and threat indices.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        
        {/* SVG Grid */}
        <div className="xl:col-span-3">
          <Card className="glass-card p-4 shadow-lg overflow-hidden bg-slate-950 border-slate-200/50 dark:border-slate-800/50">
            <div className="relative aspect-video w-full rounded-xl border border-slate-900 bg-slate-950 overflow-hidden">
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:30px_30px] opacity-15" />
              
              <svg viewBox={`0 0 ${mapWidth} ${mapHeight}`} className="w-full h-full relative z-10 select-none">
                {/* Sector paths */}
                <path d="M 50,100 Q 300,50 700,90 T 750,400" fill="none" stroke="rgba(71,85,105,0.25)" strokeWidth="6" />
                <path d="M 200,20 Q 250,220 300,430" fill="none" stroke="rgba(71,85,105,0.2)" strokeWidth="4" />
                <path d="M 50,320 L 780,290" fill="none" stroke="rgba(71,85,105,0.2)" strokeWidth="5" />

                {/* Heat nodes */}
                {heatmap.map((pin) => {
                  const { x, y } = getXY(pin.lat, pin.lng);
                  const baseRadius = Math.max(15, Math.min(pin.count * 1.5, 45));
                  const isSelected = selectedPin?.name === pin.name;

                  return (
                    <g key={pin.name}>
                      <circle
                        cx={x}
                        cy={y}
                        r={baseRadius}
                        fill="rgba(239,68,68,0.15)"
                        className="animate-ping"
                        style={{ transformOrigin: `${x}px ${y}px`, animationDuration: '3.5s' }}
                      />
                      <circle
                        cx={x}
                        cy={y}
                        r={baseRadius * 0.8}
                        fill="rgba(239,68,68,0.25)"
                        stroke="rgba(239,68,68,0.5)"
                        strokeWidth="1.5"
                        onClick={() => setSelectedPin(pin)}
                        className="cursor-pointer hover:fill-red-500/40 hover:stroke-red-500 transition-all duration-200"
                      />
                      <circle
                        cx={x}
                        cy={y}
                        r="5"
                        fill={isSelected ? "#ffffff" : "#ef4444"}
                        stroke="#000000"
                        strokeWidth="1"
                      />
                    </g>
                  );
                })}
              </svg>
              <div className="absolute bottom-4 left-4 p-2 bg-black/60 rounded border border-white/10 text-[9px] font-bold text-slate-400 backdrop-blur z-20 flex flex-col gap-1">
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-red-500/45 border border-red-500"></span> Violation Hotspots</span>
                <span>Delhi Sector 1</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Selected info card */}
        <div>
          {selectedPin ? (
            <Card className="glass-card p-5 space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-200/40 dark:border-slate-800/40 pb-3">
                <MapPin size={18} className="text-red-500" />
                <div className="min-w-0">
                  <h3 className="font-extrabold text-sm truncate max-w-[130px]">{selectedPin.name}</h3>
                  <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block">Hotspot Checkpoint</span>
                </div>
              </div>

              <div className="space-y-3 text-xs font-semibold">
                <div className="flex justify-between">
                  <span className="text-slate-400">Position GPS</span>
                  <span className="font-mono text-slate-600 dark:text-slate-350">
                    {selectedPin.lat.toFixed(4)}°N, {selectedPin.lng.toFixed(4)}°E
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Offences</span>
                  <span className="text-red-500 font-extrabold">{selectedPin.count} events</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Risk Tier</span>
                  <Badge variant={selectedPin.count > 25 ? "destructive" : "secondary"}>
                    {selectedPin.count > 25 ? "High Threat" : "Moderate"}
                  </Badge>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-100/50 dark:bg-slate-900/60 border border-slate-200/40 dark:border-slate-800/40 text-[10px] text-slate-500 dark:text-slate-400 space-y-1">
                <div className="flex items-center gap-1 font-bold text-slate-700 dark:text-slate-300">
                  <Info size={12} className="text-blue-500" />
                  <span>Deployment Memo</span>
                </div>
                <p className="leading-relaxed font-semibold">
                  This sector logs high frequencies of overspeeding and red light crossings. Allocate extra CCTV checks.
                </p>
              </div>
            </Card>
          ) : (
            <Card className="glass-card p-5 text-center py-10 text-xs text-slate-400 font-bold">
              Select a hotspot node on the map view.
            </Card>
          )}
        </div>

      </div>
    </div>
  );
}

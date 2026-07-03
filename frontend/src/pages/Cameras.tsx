import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog";
import { Plus, Camera, VideoOff, Trash2, MapPin } from "lucide-react";

interface CameraItem {
  id: string
  name: string
  location: string
  ip_address?: string | null
  status: string
  health_status: string
  lat: number
  lng: number
}

// Fallback cameras
const fallbackCams: CameraItem[] = [
  { id: "CAM-001", name: "Connaught Place Circular", location: "Connaught Place, New Delhi", status: "online", health_status: "good", lat: 28.6304, lng: 77.2177 },
  { id: "CAM-002", name: "India Gate Ring Road", location: "Rajpath, New Delhi", status: "online", health_status: "good", lat: 28.6129, lng: 77.2295 },
  { id: "CAM-003", name: "Rajouri Garden Checkpoint", location: "Rajouri Garden, New Delhi", status: "online", health_status: "warning", lat: 28.6415, lng: 77.1245 },
  { id: "CAM-004", name: "AIIMS Crossing Main Feed", location: "Ring Road, AIIMS, New Delhi", status: "offline", health_status: "critical", lat: 28.5672, lng: 77.2100 }
];

export default function Cameras() {
  const { token, user } = useContext(AuthContext);
  const [cameras, setCameras] = useState<CameraItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Form Modal
  const [addModal, setAddModal] = useState<boolean>(false);
  const [camId, setCamId] = useState("");
  const [camName, setCamName] = useState("");
  const [camLoc, setCamLoc] = useState("");
  const [camIp, setCamIp] = useState("");
  const [camLat, setCamLat] = useState("");
  const [camLng, setCamLng] = useState("");
  const [formErr, setFormErr] = useState("");

  const fetchCameras = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/cameras`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCameras(data);
      } else {
        throw new Error("API Offline");
      }
    } catch (err) {
      console.warn("Using offline cameras registry.");
      setCameras(fallbackCams);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, [token]);

  const handleToggleStatusSubmit = async (cam: CameraItem) => {
    if (user?.role !== "admin") return;

    const newStatus = cam.status === "online" ? "offline" : "online";
    const newHealth = newStatus === "online" ? "good" : "critical";

    try {
      const res = await fetch(`${API_BASE_URL}/cameras/${cam.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus, health_status: newHealth }),
      });
      if (res.ok) fetchCameras();
    } catch (err) {
      console.warn("API Offline. Toggling camera status locally.");
      setCameras((prev) =>
        prev.map((c) =>
          c.id === cam.id ? { ...c, status: newStatus, health_status: newHealth } : c
        )
      );
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErr("");

    if (!camId || !camName || !camLoc || !camLat || !camLng) {
      setFormErr("Please fill all required coordinates fields.");
      return;
    }

    const payload = {
      id: camId,
      name: camName,
      location: camLoc,
      ip_address: camIp || null,
      lat: parseFloat(camLat),
      lng: parseFloat(camLng),
      status: "online",
      health_status: "good"
    };

    try {
      const res = await fetch(`${API_BASE_URL}/cameras`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setAddModal(false);
        setCamId(""); setCamName(""); setCamLoc(""); setCamIp(""); setCamLat(""); setCamLng("");
        fetchCameras();
      } else {
        const data = await res.json();
        setFormErr(data.detail || "Registration failed.");
      }
    } catch (err) {
      console.warn("API Offline. Appending new camera locally (simulation).");
      const localNew: CameraItem = {
        ...payload,
        status: "online",
        health_status: "good"
      };
      setCameras((prev) => [localNew, ...prev]);
      setAddModal(false);
      setCamId(""); setCamName(""); setCamLoc(""); setCamIp(""); setCamLat(""); setCamLng("");
    }
  };

  const handleDeleteCameraSubmit = async (id: string) => {
    if (!window.confirm(`Delete camera ${id}?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/cameras/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) fetchCameras();
    } catch (err) {
      console.warn("API Offline. Deleting camera locally.");
      setCameras((prev) => prev.filter((c) => c.id !== id));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Camera Deployments</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Monitor camera checklist streams health and coordinate parameters.
          </p>
        </div>
        {user?.role === "admin" && (
          <Button
            onClick={() => setAddModal(true)}
            className="text-xs font-bold py-2 h-9"
          >
            <Plus size={14} className="mr-1.5" />
            Register Camera
          </Button>
        )}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {loading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="h-44 rounded-2xl bg-slate-200 dark:bg-slate-800 animate-pulse"></div>
          ))
        ) : cameras.length === 0 ? (
          <div className="md:col-span-2 xl:col-span-3 text-center py-20 text-slate-400 font-bold text-sm">
            No cameras registered.
          </div>
        ) : (
          cameras.map((cam) => (
            <Card
              key={cam.id}
              className="glass-card flex flex-col justify-between p-5"
            >
              <div className="space-y-3.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-900 text-slate-400">
                    {cam.id}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className={`h-1.5 w-1.5 rounded-full ${cam.status === "online" ? "bg-emerald-500" : "bg-red-500"}`} />
                    <span className="text-[9px] font-bold uppercase text-slate-400">{cam.status}</span>
                  </div>
                </div>

                <div>
                  <h3 className="font-extrabold text-xs">{cam.name}</h3>
                  <span className="text-[10px] text-slate-550 dark:text-slate-400 font-semibold flex items-center gap-1 mt-0.5">
                    <MapPin size={10} className="shrink-0" />
                    {cam.location}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px] font-semibold border-t border-slate-150/30 dark:border-slate-800/40 pt-3">
                  <div>
                    <span className="text-slate-450 block">IP Stream</span>
                    <span className="font-mono">{cam.ip_address || "MOCK_SIMULATOR"}</span>
                  </div>
                  <div>
                    <span className="text-slate-450 block">Diagnose Status</span>
                    <span className={`font-bold capitalize ${cam.health_status === "good" ? "text-emerald-500" : cam.health_status === "warning" ? "text-amber-500" : "text-red-500"}`}>
                      {cam.health_status}
                    </span>
                  </div>
                </div>
              </div>

              {user?.role === "admin" && (
                <div className="flex items-center justify-between border-t border-slate-150/30 dark:border-slate-800/40 pt-3 mt-4 text-[10px] font-bold">
                  <Button
                    onClick={() => handleToggleStatusSubmit(cam)}
                    variant="outline"
                    className="h-8 py-1 px-3 text-[10px]"
                  >
                    {cam.status === "online" ? (
                      <>
                        <VideoOff size={12} className="mr-1" />
                        Deactivate
                      </>
                    ) : (
                      <>
                        <Camera size={12} className="mr-1" />
                        Activate
                      </>
                    )}
                  </Button>
                  <Button
                    onClick={() => handleDeleteCameraSubmit(cam.id)}
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 text-red-500 hover:bg-red-500/10"
                  >
                    <Trash2 size={12} />
                  </Button>
                </div>
              )}
            </Card>
          ))
        )}
      </div>

      {/* dialog modal */}
      <Dialog open={addModal} onOpenChange={setAddModal}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-sm font-bold text-white">Register CCTV checkpoint</DialogTitle>
            <DialogDescription className="text-[10px] text-slate-400">
              Establish checkpoint mappings coordinates for AI models.
            </DialogDescription>
          </DialogHeader>

          {formErr && (
            <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-2.5 text-[10px] text-red-400 font-bold">
              {formErr}
            </div>
          )}

          <form onSubmit={handleRegisterSubmit} className="space-y-3.5 mt-2">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">Camera ID *</label>
                <Input type="text" required placeholder="CAM-101" value={camId} onChange={(e) => setCamId(e.target.value)} className="h-9 text-xs text-white" />
              </div>
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">Camera Name *</label>
                <Input type="text" required placeholder="India Gate Check 2" value={camName} onChange={(e) => setCamName(e.target.value)} className="h-9 text-xs text-white" />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-400 uppercase">Location *</label>
              <Input type="text" required placeholder="Rajpath Circle, New Delhi" value={camLoc} onChange={(e) => setCamLoc(e.target.value)} className="h-9 text-xs text-white" />
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-400 uppercase">IP Stream Address</label>
              <Input type="text" placeholder="192.168.10.15" value={camIp} onChange={(e) => setCamIp(e.target.value)} className="h-9 text-xs text-white" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">Latitude *</label>
                <Input type="number" step="0.000001" required placeholder="28.6304" value={camLat} onChange={(e) => setCamLat(e.target.value)} className="h-9 text-xs text-white" />
              </div>
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-400 uppercase">Longitude *</label>
                <Input type="number" step="0.000001" required placeholder="77.2177" value={camLng} onChange={(e) => setCamLng(e.target.value)} className="h-9 text-xs text-white" />
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setAddModal(false)}>Cancel</Button>
              <Button type="submit" size="sm">Save Camera</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

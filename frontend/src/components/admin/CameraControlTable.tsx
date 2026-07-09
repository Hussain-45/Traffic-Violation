import React, { useState } from "react";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";

interface CameraItem {
  id: str;
  name: string;
  location: string;
  ip_address: string | null;
  status: string;
  health_status: string;
  lat: number;
  lng: number;
  is_active_feed: boolean;
  fps: number;
  resolution: string;
}

interface CameraTableProps {
  cameras: CameraItem[];
  onToggle: (id: string, enabled: boolean) => Promise<void>;
  onRestart: (id: string) => Promise<void>;
}

export function CameraControlTable({ cameras, onToggle, onRestart }: CameraTableProps) {
  const [selectedCam, setSelectedCam] = useState<CameraItem | null>(null);

  const getHealthBadge = (health: string) => {
    switch (health) {
      case "good":
        return <Badge variant="success">GOOD</Badge>;
      case "warning":
        return <Badge variant="warning">WARNING</Badge>;
      case "critical":
        return <Badge variant="danger">CRITICAL</Badge>;
      default:
        return <Badge variant="info">UNKNOWN</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="overflow-x-auto rounded-lg border border-navy-accent/50 bg-navy-light">
        <table className="w-full text-left border-collapse text-sm text-slate-300">
          <thead>
            <tr className="bg-navy-dark border-b border-navy-accent/40 text-slate-400 font-semibold uppercase text-xs">
              <th className="p-4">Camera Details</th>
              <th className="p-4">Location</th>
              <th className="p-4">IP Address</th>
              <th className="p-4">Status</th>
              <th className="p-4">Health</th>
              <th className="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-accent/30">
            {cameras.map((cam) => (
              <tr key={cam.id} className="hover:bg-navy-dark/40 transition-colors">
                <td className="p-4 font-medium text-slate-100">
                  <div>{cam.name}</div>
                  <div className="text-xs text-slate-500 font-mono mt-0.5">{cam.id}</div>
                </td>
                <td className="p-4 text-slate-400">{cam.location}</td>
                <td className="p-4 font-mono text-slate-400">{cam.ip_address || "None"}</td>
                <td className="p-4">
                  <span className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${cam.status === 'online' ? 'bg-status-green animate-pulse' : 'bg-status-red'}`} />
                    <span className="capitalize">{cam.status}</span>
                  </span>
                </td>
                <td className="p-4">{getHealthBadge(cam.health_status)}</td>
                <td className="p-4 text-right space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedCam(cam)}
                  >
                    🔍 Preview
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onRestart(cam.id)}
                  >
                    🔄 Restart
                  </Button>
                  <Button
                    variant={cam.status === "online" ? "danger" : "primary"}
                    size="sm"
                    onClick={() => onToggle(cam.id, cam.status !== "online")}
                  >
                    {cam.status === "online" ? "Disable" : "Enable"}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Preview Dialog Modal */}
      {selectedCam && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-navy-light rounded-lg border border-navy-accent max-w-2xl w-full overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-navy-accent/50 flex items-center justify-between">
              <h3 className="font-bold text-slate-100 text-base">{selectedCam.name} — Live Feed</h3>
              <button
                className="p-1 text-slate-400 hover:text-white rounded cursor-pointer"
                onClick={() => setSelectedCam(null)}
              >
                ✕
              </button>
            </div>
            <div className="p-6">
              {selectedCam.status === "online" ? (
                <div className="aspect-video w-full rounded bg-black flex items-center justify-center relative overflow-hidden group">
                  <div className="absolute top-4 left-4 text-xs font-mono text-brand-cyan bg-navy-darker/80 px-2 py-1 rounded border border-navy-accent/50">
                    LIVE Feed Node: {selectedCam.id}
                  </div>
                  {selectedCam.is_active_feed ? (
                    <img
                      src={`http://localhost:8000/api/v1/camera/stream?t=${Date.now()}`}
                      alt="Camera Feed"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-center text-slate-400">
                      <div className="text-2xl mb-2">🎥</div>
                      <div>Standard JPEG feed snapshot active</div>
                      <div className="text-xs text-slate-500 mt-1 font-mono">
                        ({selectedCam.resolution} @ {selectedCam.fps || 30} FPS)
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="aspect-video w-full rounded bg-navy-dark flex flex-col items-center justify-center text-slate-500">
                  <div className="text-4xl mb-3">📴</div>
                  <div className="text-sm font-semibold">Camera Node is Offline</div>
                  <div className="text-xs text-slate-600 mt-1">Enable camera stream node to start live monitoring feeds.</div>
                </div>
              )}
            </div>
            <div className="p-4 border-t border-navy-accent/50 flex justify-end">
              <Button variant="secondary" onClick={() => setSelectedCam(null)}>
                Close Preview
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

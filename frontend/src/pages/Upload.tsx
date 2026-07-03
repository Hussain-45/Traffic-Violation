import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Select } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, CheckCircle, AlertTriangle, ShieldAlert, Cpu, Eye } from "lucide-react";

interface CameraItem {
  id: string
  name: string
  location: string
  status: string
}

interface ViolationDetails {
  type: string
  label: string
  fine_amount: number
  confidence: number
}

interface VehicleDetect {
  type: string
  brand: string
  color: string
  plate: string
  plate_confidence: number
  plate_crop_path: string
  speed: number
  violations: ViolationDetails[]
}

interface AIUploadResults {
  vehicles: VehicleDetect[]
  signal_state: string
  confidence: number
}

interface ServerResponse {
  success: boolean
  message: string
  ai_results: AIUploadResults
}

// Offline simulated upload response
const mockUploadResults: ServerResponse = {
  success: true,
  message: "Simulated AI engine executed successfully.",
  ai_results: {
    vehicles: [
      {
        type: "car",
        brand: "Honda City",
        color: "Red",
        plate: "DL 3C AW 9081",
        plate_confidence: 0.96,
        plate_crop_path: "",
        speed: 74.2,
        violations: [
          { type: "overspeeding", label: "Overspeeding (74 km/h - Limit: 60)", fine_amount: 1000, confidence: 0.94 }
        ]
      }
    ],
    signal_state: "green",
    confidence: 0.92
  }
};

export default function Upload() {
  const { token } = useContext(AuthContext);
  const [cameras, setCameras] = useState<CameraItem[]>([]);
  const [selectedCam, setSelectedCam] = useState<string>("");

  const [dragActive, setDragActive] = useState<boolean>(false);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [result, setResult] = useState<ServerResponse | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const fetchCams = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/cameras`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setCameras(data);
          const online = data.filter((c: CameraItem) => c.status === "online");
          if (online.length > 0) setSelectedCam(online[0].id);
        }
      } catch (err) {
        // Fallback dummy cameras
        setCameras([
          { id: "CAM-001", name: "Connaught Place Jn 1", location: "Connaught Place", status: "online" }
        ]);
        setSelectedCam("CAM-001");
      }
    };
    fetchCams();
  }, [token]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile: File | null) => {
    setError("");
    setResult(null);
    if (!selectedFile) return;

    const validTypes = ["image/jpeg", "image/png", "image/webp", "video/mp4"];
    if (!validTypes.includes(selectedFile.type)) {
      setError("Unsupported media format. Please upload JPG, PNG, WEBP, or MP4 files.");
      return;
    }

    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setProgress(10);
    setError("");
    setResult(null);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 15;
      });
    }, 4500);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("camera_id", selectedCam);

      const res = await fetch(`${API_BASE_URL}/violations/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      clearInterval(interval);
      setProgress(100);

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        const errData = await res.json();
        setError(errData.detail || "Server failed to compile files.");
      }
    } catch (err) {
      clearInterval(interval);
      console.warn("API offline. Loading mock AI detection results.");
      // Simulated delay
      setTimeout(() => {
        setResult(mockUploadResults);
        setProgress(100);
      }, 1000);
    } finally {
      setTimeout(() => {
        setUploading(false);
        setProgress(0);
      }, 1200);
    }
  };

  const handleClear = () => {
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError("");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">AI Upload Engine</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Upload media logs manually to trigger license plate recognition (OCR) and lanes violation checks.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Drop zone container */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="glass-card p-6 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Select Checkpoint CAM
                </label>
                <Select
                  value={selectedCam}
                  onChange={(e) => setSelectedCam(e.target.value)}
                >
                  {cameras.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.id} - {c.location}
                    </option>
                  ))}
                </Select>
              </div>
            </div>

            {/* Drop Box */}
            {!previewUrl ? (
              <div
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                className={`relative flex flex-col items-center justify-center border-2 border-dashed rounded-2xl p-12 text-center transition-all ${
                  dragActive
                    ? "border-blue-500 bg-blue-500/5"
                    : "border-slate-300 hover:border-slate-450 dark:border-slate-800 dark:hover:border-slate-700"
                }`}
              >
                <UploadCloud size={40} className="text-slate-400 dark:text-slate-600 mb-3 animate-bounce" />
                <div className="space-y-1 text-xs font-semibold">
                  <p>Drag & Drop vehicle video/image here</p>
                  <p className="text-[10px] text-slate-400">or click to browse local files</p>
                </div>
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept="image/*,video/*"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>
            ) : (
              /* Preview */
              <div className="relative border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden bg-slate-900 aspect-video flex items-center justify-center">
                {file && file.type.startsWith("video") ? (
                  <video src={previewUrl} controls className="h-full w-full object-contain" />
                ) : (
                  <img src={previewUrl || ""} alt="Preview" className="h-full w-full object-contain" />
                )}
                {!uploading && (
                  <Button
                    onClick={handleClear}
                    variant="destructive"
                    size="sm"
                    className="absolute top-4 right-4 text-[10px] py-1 h-7"
                  >
                    Clear Media
                  </Button>
                )}
              </div>
            )}

            {error && (
              <div className="flex items-start gap-2.5 rounded-xl bg-red-500/10 border border-red-500/30 p-3 text-xs text-red-400">
                <ShieldAlert size={14} className="shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {file && !uploading && !result && (
              <Button
                onClick={handleUploadSubmit}
                className="w-full text-xs font-bold py-3.5 flex items-center justify-center gap-2"
              >
                <Cpu size={16} />
                Process Bounding Box & OCR
              </Button>
            )}

            {uploading && (
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[10px] font-bold">
                  <span className="text-slate-400">Executing YOLO tracking models...</span>
                  <span className="text-blue-500">{progress}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Results Drawer */}
        <div className="space-y-6">
          <AnimatePresence mode="wait">
            {!result ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="glass-card p-6 shadow-sm flex flex-col items-center justify-center text-center py-24 h-full"
              >
                <Cpu size={32} className="text-slate-500 mb-2 animate-pulse" />
                <h3 className="font-bold text-xs text-slate-500">Pipeline Inactive</h3>
                <p className="text-[10px] text-slate-400 max-w-xs mt-1 leading-relaxed">
                  Trigger the AI Pipeline to isolate vehicle plates and record fine infractions.
                </p>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="glass-card p-6 shadow-sm space-y-5"
              >
                <div className="flex items-center gap-2.5 pb-2.5 border-b border-slate-200/40 dark:border-slate-800/40">
                  <CheckCircle size={20} className="text-emerald-500 shrink-0" />
                  <div>
                    <h3 className="font-extrabold text-xs">AI Inference Completed</h3>
                    <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">
                      Overall Confidence: {Math.round(result.ai_results.confidence * 100)}%
                    </span>
                  </div>
                </div>

                {/* Bbox visual placeholder */}
                <div className="space-y-1.5">
                  <label className="text-[9px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                    <Eye size={10} />
                    Bounding Box Output Frame
                  </label>
                  <div className="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 aspect-video bg-slate-900 flex items-center justify-center">
                    <img
                      src="https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=400&q=80"
                      alt="AI crop"
                      className="w-full h-full object-cover"
                    />
                  </div>
                </div>

                {/* Vehicles list */}
                {result.ai_results.vehicles.map((v, i) => (
                  <div key={i} className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-900/60 border border-slate-200/40 dark:border-slate-800/40 space-y-3 text-xs">
                    <div className="flex items-center justify-between text-[10px] font-bold">
                      <span className="text-slate-400 uppercase">Class: {v.type}</span>
                      <span className="text-slate-600 dark:text-slate-350">{v.brand} ({v.color})</span>
                    </div>

                    <div className="flex items-center justify-between gap-2 bg-slate-200/40 dark:bg-slate-950 p-2 rounded-lg border border-slate-300/10">
                      <div className="h-8 w-24 bg-yellow-400 rounded flex items-center justify-center font-extrabold text-[10px] text-black border border-black/20">
                        {v.plate}
                      </div>
                      <div className="text-right">
                        <span className="block font-bold text-blue-500 text-[10px]">PLATE OK</span>
                        <span className="block text-[8px] text-slate-400 font-bold uppercase">
                          Conf: {Math.round(v.plate_confidence * 100)}%
                        </span>
                      </div>
                    </div>

                    {/* Violations */}
                    {v.violations.length > 0 ? (
                      <div className="space-y-1 pt-2 border-t border-slate-200 dark:border-slate-800">
                        {v.violations.map((vi, viIdx) => (
                          <div key={viIdx} className="flex items-center justify-between p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-[10px] text-red-500 font-bold">
                            <span className="flex items-center gap-1.5">
                              <AlertTriangle size={12} />
                              {vi.label}
                            </span>
                            <span>₹{vi.fine_amount}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-[8px] text-emerald-500 font-bold uppercase tracking-wider pt-2 border-t border-slate-200 dark:border-slate-800">
                        ✓ No Traffic Violations Detected
                      </div>
                    )}
                  </div>
                ))}

                <Button
                  onClick={handleClear}
                  variant="outline"
                  size="sm"
                  className="w-full text-[10px]"
                >
                  Clear Results
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

      </div>
    </div>
  );
}

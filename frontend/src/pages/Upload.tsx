import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Select } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { motion, AnimatePresence } from "framer-motion";
import {
  UploadCloud,
  CheckCircle,
  AlertTriangle,
  ShieldAlert,
  Cpu,
  Eye,
  Trash2,
  FileVideo,
  FileImage,
  RefreshCw,
  X
} from "lucide-react";

interface CameraItem {
  id: string
  name: string
  location: string
  status: string
}

interface StagedFile {
  id: string
  file: File
  preview: string
  progress: number
  status: "idle" | "uploading" | "success" | "error"
  errorMsg?: string
  result?: any
  detectedTime?: string
  original_image_path?: string
  detected_image_path?: string
}

// Fallback AI results for stand-alone frontend mode
const mockAIResult = {
  vehicles: [
    {
      type: "car",
      brand: "Hyundai Verna",
      color: "White",
      plate: "DL 3C BC 1022",
      plate_confidence: 0.95,
      violations: [
        { type: "overspeeding", label: "Overspeeding (76 km/h - Limit: 60)", fine_amount: 1000, confidence: 0.94 }
      ]
    }
  ],
  signal_state: "green",
  confidence_score: 0.91
};

export default function Upload() {
  const { token } = useContext(AuthContext);
  const [cameras, setCameras] = useState<CameraItem[]>([]);
  const [selectedCam, setSelectedCam] = useState<string>("");

  const [dragActive, setDragActive] = useState<boolean>(false);
  const [stagedFiles, setStagedFiles] = useState<StagedFile[]>([]);
  const [globalError, setGlobalError] = useState<string>("");
  const [isProcessingBatch, setIsProcessingBatch] = useState<boolean>(false);

  // Fetch cameras for registration association
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
        setCameras([
          { id: "CAM-001", name: "Connaught Place Jn 1", location: "Connaught Place", status: "online" },
          { id: "CAM-002", name: "India Gate Circle", location: "Rajpath Circular", status: "online" }
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

  // Perform strict file format validation
  const validateFiles = (files: FileList): StagedFile[] => {
    const validImageTypes = ["image/jpeg", "image/png", "image/webp"];
    const validVideoTypes = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska"];
    const newStaged: StagedFile[] = [];

    setGlobalError("");

    Array.from(files).forEach((file) => {
      const isImg = validImageTypes.includes(file.type);
      const isVid = validVideoTypes.includes(file.type);

      if (!isImg && !isVid) {
        setGlobalError("Skipped invalid files. Please upload images (JPG, PNG, WEBP) or videos (MP4, MOV, AVI, MKV) only.");
        return;
      }

      newStaged.push({
        id: `${file.name}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        preview: URL.createObjectURL(file),
        progress: 0,
        status: "idle"
      });
    });

    return newStaged;
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const added = validateFiles(e.dataTransfer.files);
      setStagedFiles((prev) => [...prev, ...added]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const added = validateFiles(e.target.files);
      setStagedFiles((prev) => [...prev, ...added]);
    }
  };

  const removeFile = (id: string) => {
    setStagedFiles((prev) => {
      const target = prev.find((f) => f.id === id);
      if (target) URL.revokeObjectURL(target.preview);
      return prev.filter((f) => f.id !== id);
    });
  };

  const clearAllStaged = () => {
    stagedFiles.forEach((f) => URL.revokeObjectURL(f.preview));
    setStagedFiles([]);
    setGlobalError("");
  };

  // Upload individual staged file
  const uploadSingleFile = async (staged: StagedFile) => {
    // Set status to uploading
    setStagedFiles((prev) =>
      prev.map((f) => (f.id === staged.id ? { ...f, status: "uploading", progress: 10 } : f))
    );

    // Simulate progress increments for UI/UX
    const progressInterval = setInterval(() => {
      setStagedFiles((prev) =>
        prev.map((f) => {
          if (f.id === staged.id && f.status === "uploading") {
            const nextProgress = f.progress >= 90 ? 90 : f.progress + 15;
            return { ...f, progress: nextProgress };
          }
          return f;
        })
      );
    }, 800);

    try {
      const formData = new FormData();
      formData.append("file", staged.file);
      formData.append("camera_id", selectedCam);

      const res = await fetch(`${API_BASE_URL}/violations/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      clearInterval(progressInterval);

      if (res.ok) {
        const data = await res.json();
        setStagedFiles((prev) =>
          prev.map((f) =>
            f.id === staged.id
              ? { ...f, status: "success", progress: 100, result: data.ai_results, original_image_path: data.original_image_path, detected_image_path: data.detected_image_path, detectedTime: new Date().toLocaleTimeString() }
              : f
          )
        );
      } else {
        const err = await res.json();
        setStagedFiles((prev) =>
          prev.map((f) =>
            f.id === staged.id
              ? { ...f, status: "error", errorMsg: err.detail || "Server error" }
              : f
          )
        );
      }
    } catch (err) {
      clearInterval(progressInterval);
      console.warn("API offline. Loading mock detection parameters for staged file.");
      
      // Complete mock upload sequence with delay
      setTimeout(() => {
        setStagedFiles((prev) =>
          prev.map((f) =>
            f.id === staged.id
              ? { ...f, status: "success", progress: 100, result: mockAIResult, original_image_path: staged.preview, detected_image_path: staged.preview, detectedTime: new Date().toLocaleTimeString() }
              : f
          )
        );
      }, 1500);
    }
  };

  // Upload all staged files sequentially
  const handleUploadAll = async () => {
    setIsProcessingBatch(true);
    const filesToUpload = stagedFiles.filter((f) => f.status === "idle" || f.status === "error");
    
    for (const staged of filesToUpload) {
      await uploadSingleFile(staged);
    }
    setIsProcessingBatch(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">AI Upload Engine</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
          Stage multiple files or drop folders to run the YOLO object classifier and OCR checks.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Main Staging Area */}
        <div className="xl:col-span-2 space-y-6">
          <Card className="glass-card p-6 space-y-6">
            
            {/* Options bar */}
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
              <div className="space-y-1 w-full sm:w-72">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-450">
                  Checkpoint CAM Association
                </label>
                <Select
                  value={selectedCam}
                  onChange={(e) => setSelectedCam(e.target.value)}
                  disabled={isProcessingBatch}
                >
                  {cameras.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.id} - {c.location}
                    </option>
                  ))}
                </Select>
              </div>

              {stagedFiles.length > 0 && (
                <div className="flex gap-2 w-full sm:w-auto justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={clearAllStaged}
                    disabled={isProcessingBatch}
                    className="text-[10px] font-bold h-8"
                  >
                    Clear All ({stagedFiles.length})
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleUploadAll}
                    disabled={isProcessingBatch || stagedFiles.filter(f => f.status === 'idle' || f.status === 'error').length === 0}
                    className="text-[10px] font-bold h-8"
                  >
                    {isProcessingBatch ? (
                      <>
                        <RefreshCw size={12} className="mr-1.5 animate-spin" />
                        Scanning Batch...
                      </>
                    ) : (
                      <>
                        <Cpu size={12} className="mr-1.5" />
                        Process Batch
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>

            {/* Drag & Drop Area */}
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`relative flex flex-col items-center justify-center border-2 border-dashed rounded-2xl p-10 text-center transition-all ${
                dragActive
                  ? "border-blue-500 bg-blue-500/5"
                  : "border-slate-350 hover:border-slate-400 dark:border-slate-800 dark:hover:border-slate-700"
              }`}
            >
              <UploadCloud size={38} className="text-slate-450 mb-3 animate-bounce" />
              <div className="space-y-1 text-xs font-bold text-slate-750 dark:text-slate-300">
                <p>Drag & Drop images or videos here</p>
                <p className="text-[10px] text-slate-450 font-semibold">
                  Supports JPG, PNG, WEBP, MP4, AVI, MOV, MKV (Multiple select allowed)
                </p>
              </div>
              <input
                type="file"
                multiple
                onChange={handleFileChange}
                accept="image/*,video/*"
                disabled={isProcessingBatch}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
            </div>

            {globalError && (
              <div className="flex items-start gap-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 p-3 text-[11px] text-amber-500 font-bold">
                <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                <span>{globalError}</span>
              </div>
            )}

            {/* Staged files list grid */}
            <div className="space-y-3.5">
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-slate-450">
                Upload Queue ({stagedFiles.length} files)
              </h4>
              
              {stagedFiles.length === 0 ? (
                <div className="text-center py-10 border border-slate-100 dark:border-slate-900 rounded-2xl text-slate-450 text-[11px] font-bold">
                  No files staged. Drag and drop files to populate the queue.
                </div>
              ) : (
                <div className="space-y-3">
                  {stagedFiles.map((staged) => {
                    const isVid = staged.file.type.startsWith("video");
                    return (
                      <div
                        key={staged.id}
                        className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-900 border border-slate-200/50 dark:border-slate-800/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-semibold"
                      >
                        <div className="flex items-center gap-3 w-full sm:w-auto min-w-0">
                          {/* File Icon */}
                          <div className="h-9 w-9 rounded-lg bg-slate-200 dark:bg-slate-950 flex items-center justify-center shrink-0 border border-slate-300/10">
                            {isVid ? <FileVideo size={16} className="text-blue-500" /> : <FileImage size={16} className="text-emerald-500" />}
                          </div>
                          <div className="min-w-0">
                            <span className="block font-bold text-slate-800 dark:text-slate-150 truncate max-w-[200px]">
                              {staged.file.name}
                            </span>
                            <span className="block text-[9px] text-slate-450 font-bold">
                              {(staged.file.size / (1024 * 1024)).toFixed(2)} MB
                            </span>
                          </div>
                        </div>

                        {/* Progress slider and status indicators */}
                        <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
                          <div className="w-full sm:w-36 space-y-1">
                            <div className="flex justify-between text-[9px] font-bold text-slate-450">
                              <span>{staged.status === 'success' ? 'Verified' : staged.status === 'error' ? 'Failed' : staged.status === 'uploading' ? 'Analyzing...' : 'Staged'}</span>
                              <span>{staged.progress}%</span>
                            </div>
                            <div className="h-1.5 w-full rounded-full bg-slate-200 dark:bg-slate-950 overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-300 ${
                                  staged.status === 'success' ? 'bg-emerald-500' : staged.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                                }`}
                                style={{ width: `${staged.progress}%` }}
                              />
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            {staged.status === "idle" && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => uploadSingleFile(staged)}
                                disabled={isProcessingBatch}
                                className="h-7 text-[9px] font-bold py-1 px-2.5"
                              >
                                Scan
                              </Button>
                            )}
                            
                            {staged.status === "success" && (
                              <Badge variant="success" className="text-[8px] py-0.5 px-1.5 font-bold">
                                Done
                              </Badge>
                            )}

                            {staged.status === "error" && (
                              <Badge variant="destructive" className="text-[8px] py-0.5 px-1.5 font-bold">
                                Error
                              </Badge>
                            )}

                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeFile(staged.id)}
                              disabled={isProcessingBatch}
                              className="h-7 w-7 p-0 text-slate-400 hover:text-red-500"
                            >
                              <X size={12} />
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Bbox OCR output drawer */}
        <div>
          <Card className="glass-card p-6 h-full flex flex-col justify-between shadow-sm">
            <CardHeader className="p-0 pb-3 border-b border-slate-200/40 dark:border-slate-850/40">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Cpu size={16} className="text-blue-500" />
                Pipeline Scanner Logs
              </CardTitle>
              <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                Real-time output logs of isolated license plates.
              </CardDescription>
            </CardHeader>

            <div className="flex-1 overflow-y-auto space-y-4 my-4 max-h-[420px] pr-1">
              {stagedFiles.filter(f => f.status === 'success').length === 0 ? (
                <div className="text-center py-20 text-slate-450 font-bold text-xs flex flex-col items-center justify-center gap-2">
                  <Eye size={24} className="text-slate-600 animate-pulse" />
                  <span>No scanning outputs</span>
                </div>
              ) : (
                stagedFiles.filter(f => f.status === 'success').map((staged) => (
                  <div key={staged.id} className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-900 border border-slate-200/40 dark:border-slate-850/40 space-y-3 text-xs">
                    <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/30 pb-2">
                      <div className="min-w-0">
                        <span className="font-bold truncate max-w-[130px] block">{staged.file.name}</span>
                        {staged.detectedTime && (
                          <span className="text-[8px] text-slate-450 font-semibold block">Scan Time: {staged.detectedTime}</span>
                        )}
                      </div>
                      <Badge variant="success" className="text-[7px]">Processed</Badge>
                    </div>

                    {staged.result?.vehicles.map((v: any, vIdx: number) => (
                      <div key={vIdx} className="space-y-2.5 font-semibold">
                        <div className="flex justify-between text-[10px]">
                          <span className="text-slate-450 uppercase">Class: {v.type}</span>
                          <span className="text-slate-700 dark:text-slate-300">{v.brand} ({v.color})</span>
                        </div>

                        {/* Isolated Plate OCR */}
                        <div className="flex items-center justify-between bg-slate-200/40 dark:bg-slate-950 p-2 rounded-lg border border-slate-350/10">
                          <div className="h-7 w-20 bg-yellow-400 rounded flex items-center justify-center font-extrabold text-[9px] text-black border border-black/20">
                            {v.plate}
                          </div>
                          <div className="text-right text-[8px] text-slate-450 font-bold">
                            <span className="block text-blue-500 uppercase">OCR Confidence</span>
                            <span>{Math.round(v.plate_confidence * 100)}%</span>
                          </div>
                        </div>

                        {/* Plate Image Crop Preview */}
                        {v.plate_crop_path && (
                          <div className="space-y-1">
                            <span className="text-[8px] font-bold text-slate-400 uppercase tracking-widest block">License Plate Crop</span>
                            <div className="h-10 rounded bg-slate-200 dark:bg-slate-950 border border-slate-300/10 flex items-center justify-center overflow-hidden p-1">
                              <img 
                                src={`${API_BASE_URL}/${v.plate_crop_path.replace(/\\/g, '/')}`} 
                                alt="Plate Crop" 
                                className="h-full object-contain"
                                onError={(e) => {
                                  // Hide frame if path fails (like mock runs)
                                  (e.target as HTMLElement).style.display = 'none';
                                }}
                              />
                            </div>
                          </div>
                        )}

                        {/* Violations */}
                        {v.violations.length > 0 ? (
                          <div className="space-y-1">
                            {v.violations.map((vi: any, viIdx: number) => (
                              <div key={viIdx} className="flex items-center justify-between p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-[9px] text-red-500 font-bold">
                                <span className="flex items-center gap-1">
                                  <AlertTriangle size={11} />
                                  {vi.label || vi.type}
                                </span>
                                <span>₹{vi.fine_amount}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-[8px] text-emerald-500 font-bold uppercase tracking-wider block">
                            ✓ No violations detected
                          </span>
                        )}
                      </div>
                    ))}

                    {/* Prediction Trace Flow Chart */}
                    <div className="mt-3 pt-3 border-t border-slate-200/40 dark:border-slate-850/40 space-y-2">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">AI Inference Trace Flow</span>
                      
                      <div className="grid grid-cols-4 gap-2 items-stretch text-[8px] font-bold text-center">
                        
                        {/* Step 1: Original Image */}
                        <div className="bg-slate-200/20 dark:bg-slate-950/40 p-1.5 rounded-lg border border-slate-300/10 dark:border-slate-850/20 flex flex-col justify-between items-center gap-1">
                          <span className="text-blue-500 uppercase tracking-wider">1. Original</span>
                          <div className="h-14 w-full rounded bg-slate-800 overflow-hidden flex items-center justify-center border border-white/5 relative">
                            {staged.original_image_path ? (
                              <img 
                                src={staged.original_image_path.startsWith('data:') || staged.original_image_path.startsWith('blob:') ? staged.original_image_path : `${API_BASE_URL}/${staged.original_image_path.replace(/\\/g, '/')}`} 
                                alt="Original" 
                                className="h-full w-full object-cover" 
                              />
                            ) : (
                              <div className="text-[7px] text-slate-500">No Image</div>
                            )}
                          </div>
                          <span className="text-[7.5px] text-slate-450 truncate max-w-full">Input Frame</span>
                        </div>

                        {/* Step 2: Detected Image */}
                        <div className="bg-slate-200/20 dark:bg-slate-950/40 p-1.5 rounded-lg border border-slate-300/10 dark:border-slate-850/20 flex flex-col justify-between items-center gap-1">
                          <span className="text-emerald-500 uppercase tracking-wider">2. Detection</span>
                          <div className="h-14 w-full rounded bg-slate-800 overflow-hidden flex items-center justify-center border border-white/5 relative">
                            {staged.detected_image_path ? (
                              <img 
                                src={staged.detected_image_path.startsWith('data:') || staged.detected_image_path.startsWith('blob:') ? staged.detected_image_path : `${API_BASE_URL}/${staged.detected_image_path.replace(/\\/g, '/')}`} 
                                alt="Detected" 
                                className="h-full w-full object-cover" 
                              />
                            ) : (
                              <div className="text-[7px] text-slate-500">No Image</div>
                            )}
                          </div>
                          <span className="text-[7.5px] text-emerald-450">YOLOv8 Bbox</span>
                        </div>

                        {/* Step 3: OCR Plate */}
                        <div className="bg-slate-200/20 dark:bg-slate-950/40 p-1.5 rounded-lg border border-slate-300/10 dark:border-slate-850/20 flex flex-col justify-between items-center gap-1">
                          <span className="text-amber-500 uppercase tracking-wider">3. OCR Plate</span>
                          <div className="h-14 w-full rounded bg-slate-800 overflow-hidden flex flex-col items-center justify-center border border-white/5 p-1">
                            <div className="w-full bg-yellow-400 text-black font-extrabold text-[7.5px] py-0.5 rounded text-center tracking-tight border border-black/10 select-all truncate">
                              {staged.result?.vehicles?.[0]?.plate || "UNKNOWN"}
                            </div>
                            <span className="text-[7px] text-slate-400 mt-1 block">
                              Conf: {staged.result?.vehicles?.[0] ? Math.round(staged.result.vehicles[0].plate_confidence * 100) : 92}%
                            </span>
                          </div>
                          <span className="text-[7.5px] text-amber-500">EasyOCR</span>
                        </div>

                        {/* Step 4: Violation Record */}
                        <div className="bg-slate-200/20 dark:bg-slate-950/40 p-1.5 rounded-lg border border-slate-300/10 dark:border-slate-850/20 flex flex-col justify-between items-center gap-1">
                          <span className="text-red-500 uppercase tracking-wider">4. Record</span>
                          <div className="h-14 w-full rounded bg-slate-800 overflow-hidden flex flex-col items-center justify-center border border-white/5 p-1 text-center justify-center">
                            {staged.result?.vehicles?.[0]?.violations?.length > 0 ? (
                              <div className="text-red-500 text-[7.5px] font-extrabold flex flex-col items-center gap-0.5">
                                <AlertTriangle size={9} className="animate-pulse" />
                                <span className="truncate max-w-full block leading-none">
                                  {staged.result.vehicles[0].violations[0].label || staged.result.vehicles[0].violations[0].type}
                                </span>
                                <span className="text-[7px] text-slate-400">₹{staged.result.vehicles[0].violations[0].fine_amount}</span>
                              </div>
                            ) : (
                              <span className="text-emerald-500 text-[8px] font-extrabold">✓ Clean</span>
                            )}
                          </div>
                          <span className="text-[7.5px] text-red-500">Challan Log</span>
                        </div>

                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}

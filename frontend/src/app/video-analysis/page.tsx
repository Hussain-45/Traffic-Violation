"use client";

import { useAuth } from "@/components/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { useApp } from "@/lib/api";
import { BACKEND_URL } from "@/lib/apiClient";
import React, { useEffect, useState, useRef } from "react";

interface TimelineEvent {
  timestamp_sec: number;
  timestamp_str: string;
  type: string;
  plate: string;
  confidence: number;
}

interface EvidenceItem {
  evidence_id: string;
  violation_id: number;
  verified_plate: string;
  violation_type: string;
  severity: string;
  confidence: number;
  timestamp: string;
  frame_id: number;
  original_frame_path: string;
  annotated_frame_path: string;
  vehicle_crop_path: string;
  plate_crop_path: string;
}

interface Job {
  id: number;
  filename: string;
  original_video_path: string;
  processed_video_path?: string;
  thumbnail_path?: string;
  status: string;
  progress: number;
  total_frames: number;
  processed_frames: number;
  vehicles_detected: number;
  violations_detected: number;
  processing_fps: number;
  processing_time: number;
  report_path?: string;
  error_message?: string;
  created_at: string;
}

export default function VideoAnalysisPage() {
  const { token } = useAuth();
  const { backendOnline } = useApp();

  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [selectedJobResult, setSelectedJobResult] = useState<any | null>(null);
  
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedDetails, setUploadedDetails] = useState<any | null>(null);

  // Configuration settings
  const [enabledModules, setEnabledModules] = useState<string[]>([
    "vehicle_detection",
    "vehicle_tracking",
    "helmet_detection",
    "seat_belt_detection",
    "phone_detection",
    "traffic_signal_detection",
    "wrong_side_detection",
    "triple_riding_detection",
    "number_plate_detection",
    "ocr",
    "violation_engine"
  ]);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.45);
  const [maxFps, setMaxFps] = useState(30);
  const [device, setDevice] = useState("cpu");

  // Playback & UI controls
  const [showOriginal, setShowOriginal] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [showBoxes, setShowBoxes] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const originalVideoRef = useRef<HTMLVideoElement>(null);
  const processedVideoRef = useRef<HTMLVideoElement>(null);

  const triggerToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchJobs = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/video/jobs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch {
      triggerToast("Error loading historical jobs list.", "error");
    }
  };

  useEffect(() => {
    if (token) {
      fetchJobs();
    }
  }, [token, backendOnline]);

  // Status Polling for active jobs
  useEffect(() => {
    if (!token || !jobs.some(j => j.status === "processing" || j.status === "pending")) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/video/jobs`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setJobs(data);
          
          // Keep selected job updated live
          if (selectedJob) {
            const updatedSelected = data.find((j: Job) => j.id === selectedJob.id);
            if (updatedSelected) {
              setSelectedJob(updatedSelected);
              if (updatedSelected.status === "completed" && selectedJob.status !== "completed") {
                triggerToast("Video Analysis completed successfully!");
                handleOpenJob(updatedSelected);
              }
            }
          }
        }
      } catch {}
    }, 2500);

    return () => clearInterval(interval);
  }, [jobs, selectedJob, token]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    if (uploading) return;
    const file = e.dataTransfer.files[0];
    if (file) {
      await uploadVideoFile(file);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await uploadVideoFile(file);
    }
  };

  const uploadVideoFile = async (file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (!ext || !["mp4", "avi", "mov", "mkv"].includes(ext)) {
      triggerToast("Unsupported video file format. Use MP4, AVI, MOV or MKV.", "error");
      return;
    }

    if (file.size > 2 * 1024 * 1024 * 1024) {
      triggerToast("File size exceeds 2 GB limit.", "error");
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${BACKEND_URL}/api/v1/video/upload`, true);
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(percent);
        }
      };

      xhr.onload = () => {
        setUploading(false);
        if (xhr.status === 200) {
          const details = JSON.parse(xhr.responseText);
          setUploadedDetails(details);
          triggerToast("Video uploaded successfully.");
        } else {
          triggerToast("Failed to upload video to server.", "error");
        }
      };

      xhr.onerror = () => {
        setUploading(false);
        triggerToast("Connection error uploading video file.", "error");
      };

      xhr.send(formData);
    } catch {
      setUploading(false);
      triggerToast("Error triggering upload.", "error");
    }
  };

  const handleStartAnalysis = async () => {
    if (!uploadedDetails || !token) return;

    try {
      const payload = {
        filename: uploadedDetails.saved_filename,
        enabled_modules: enabledModules,
        confidence_threshold: confidenceThreshold,
        max_fps: maxFps,
        device: device
      };

      const res = await fetch(`${BACKEND_URL}/api/v1/video/analyze`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const job = await res.json();
        setSelectedJob(job);
        setSelectedJobResult(null);
        setUploadedDetails(null);
        fetchJobs();
        triggerToast("Analysis task enqueued in background.");
      } else {
        triggerToast("Failed to start analysis job.", "error");
      }
    } catch {
      triggerToast("Error launching analysis.", "error");
    }
  };

  const handleOpenJob = async (job: Job) => {
    setSelectedJob(job);
    if (job.status !== "completed") {
      setSelectedJobResult(null);
      return;
    }

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/video/result/${job.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const result = await res.json();
        setSelectedJobResult(result);
      }
    } catch {
      triggerToast("Failed to retrieve analysis results.", "error");
    }
  };

  const handleDeleteJob = async (jobId: number) => {
    if (!window.confirm("Are you sure you want to delete this video analysis job? This deletes all evidence and output videos.")) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/video/job/${jobId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        triggerToast("Job deleted.");
        if (selectedJob?.id === jobId) {
          setSelectedJob(null);
          setSelectedJobResult(null);
        }
        fetchJobs();
      }
    } catch {
      triggerToast("Error deleting job.", "error");
    }
  };

  const handleSeek = (sec: number) => {
    const video = showOriginal ? originalVideoRef.current : processedVideoRef.current;
    if (video) {
      video.currentTime = sec;
      video.play();
    }
  };

  const handleStep = (direction: "forward" | "backward") => {
    const video = showOriginal ? originalVideoRef.current : processedVideoRef.current;
    if (video) {
      video.pause();
      // Step roughly 1 frame (assuming 30fps = 0.033s)
      video.currentTime += direction === "forward" ? 0.033 : -0.033;
    }
  };

  const handleDownloadReport = () => {
    if (!selectedJob?.report_path) return;
    const link = document.createElement("a");
    link.href = `${BACKEND_URL}${selectedJob.report_path}`;
    link.download = selectedJob.report_path.split("/").pop() || "report.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadVideo = () => {
    if (!selectedJob) return;
    const link = document.createElement("a");
    link.href = `${BACKEND_URL}/api/v1/video/download/${selectedJob.id}`;
    link.download = `annotated_${selectedJob.filename}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const toggleModule = (modName: string) => {
    setEnabledModules(prev =>
      prev.includes(modName) ? prev.filter(m => m !== modName) : [...prev, modName]
    );
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-xl text-white text-xs font-semibold flex items-center gap-2 ${
          toast.type === "success" ? "bg-emerald-600" : "bg-rose-600"
        }`}>
          <span>{toast.type === "success" ? "✓" : "⚠️"}</span>
          <span>{toast.message}</span>
        </div>
      )}

      <PageHeader
        title="Offline Video Analysis"
        description="Upload traffic camera videos, execute pipelines, draw bounding boxes, and extract citation history."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* PANEL 1: Upload & Config */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>1. Upload Video Source</CardTitle>
            </CardHeader>
            <CardContent>
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className="border-2 border-dashed border-navy-accent/50 hover:border-brand-cyan/60 rounded-xl p-6 text-center transition-colors cursor-pointer bg-navy-dark/30 flex flex-col items-center justify-center min-h-[160px]"
              >
                <span className="text-3xl mb-2">📥</span>
                <span className="text-sm font-semibold text-slate-300">Drag & Drop Traffic Video</span>
                <span className="text-[10px] text-slate-500 mt-1">MP4, AVI, MOV or MKV (Max 2GB)</span>
                
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".mp4,.avi,.mov,.mkv"
                  className="hidden"
                  id="video-upload-file"
                  disabled={uploading}
                />
                <label
                  htmlFor="video-upload-file"
                  className="mt-4 px-4 py-1.5 bg-brand-blue/20 hover:bg-brand-blue/30 text-brand-cyan text-xs font-bold rounded-lg border border-brand-blue/45 transition-colors cursor-pointer"
                >
                  Choose Video
                </label>
              </div>

              {uploading && (
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                    <span>Uploading file...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-navy-accent/20 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-brand-cyan h-full transition-all duration-200" style={{ width: `${uploadProgress}%` }} />
                  </div>
                </div>
              )}

              {uploadedDetails && (
                <div className="mt-4 bg-navy-light/45 p-3 rounded-lg border border-navy-accent/30 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500">File Name:</span>
                    <span className="text-slate-300 font-mono select-all truncate max-w-[180px]">{uploadedDetails.filename}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Resolution:</span>
                    <span className="text-slate-300 font-mono">{uploadedDetails.resolution}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">FPS:</span>
                    <span className="text-slate-300 font-mono">{uploadedDetails.fps}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Duration:</span>
                    <span className="text-slate-300 font-mono">{uploadedDetails.duration}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">File Size:</span>
                    <span className="text-slate-300 font-mono">{(uploadedDetails.size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
                  </div>
                  <Button variant="primary" className="w-full mt-3 text-xs" onClick={handleStartAnalysis}>
                    Start Analysis
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>2. Pipeline Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="space-y-2.5">
                <span className="font-semibold text-slate-400 uppercase tracking-wide text-[10px] block">Active Modules</span>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: "helmet_detection", label: "Helmet Detection" },
                    { id: "seat_belt_detection", label: "Seatbelt Detection" },
                    { id: "phone_detection", label: "Mobile Phone" },
                    { id: "triple_riding_detection", label: "Triple Riding" },
                    { id: "wrong_side_detection", label: "Wrong Direction" },
                    { id: "traffic_signal_detection", label: "Red Light Jump" }
                  ].map(mod => (
                    <label key={mod.id} className="flex items-center gap-2 text-slate-300 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={enabledModules.includes(mod.id)}
                        onChange={() => toggleModule(mod.id)}
                        className="rounded bg-navy-dark border-navy-accent/50 text-brand-cyan focus:ring-0 cursor-pointer"
                      />
                      <span>{mod.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-slate-400 text-[10px] uppercase font-semibold">
                  <span>Confidence Limit</span>
                  <span className="font-mono text-brand-cyan">{confidenceThreshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.95"
                  step="0.05"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                  className="w-full h-1 bg-navy-accent/30 rounded-lg appearance-none cursor-pointer accent-brand-cyan"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold">Max Frame Rate</span>
                  <select
                    value={maxFps}
                    onChange={(e) => setMaxFps(parseInt(e.target.value))}
                    className="w-full bg-navy-dark border border-navy-accent/50 text-slate-300 text-xs rounded p-1"
                  >
                    <option value={10}>10 FPS (Fast)</option>
                    <option value={20}>20 FPS</option>
                    <option value={30}>30 FPS (Standard)</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] uppercase text-slate-400 font-semibold">Hardware Dev</span>
                  <select
                    value={device}
                    onChange={(e) => setDevice(e.target.value)}
                    className="w-full bg-navy-dark border border-navy-accent/50 text-slate-300 text-xs rounded p-1"
                  >
                    <option value="cpu">Intel CPU (PyTorch)</option>
                    <option value="gpu">Nvidia GPU (CUDA)</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* PANEL 2: Video Viewer & Timeline */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle>3. Processing Viewer & Output Monitor</CardTitle>
              {selectedJob && (
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="text-xs" onClick={() => setShowOriginal(!showOriginal)}>
                    {showOriginal ? "👁️ View Processed" : "👁️ View Original"}
                  </Button>
                  {selectedJob.status === "completed" && (
                    <Button variant="outline" size="sm" className="text-xs" onClick={handleDownloadVideo}>
                      📥 Download Output
                    </Button>
                  )}
                </div>
              )}
            </CardHeader>
            <CardContent>
              {selectedJob ? (
                <div className="space-y-4">
                  {/* Video Containers */}
                  <div className="relative aspect-video rounded-xl bg-black overflow-hidden border border-navy-accent/40 shadow-inner flex items-center justify-center">
                    {showOriginal ? (
                      <video
                        ref={originalVideoRef}
                        src={`${BACKEND_URL}/data/uploads/videos/input/${selectedJob.filename}`}
                        controls
                        className="w-full h-full object-contain"
                      />
                    ) : selectedJob.processed_video_path ? (
                      <video
                        ref={processedVideoRef}
                        src={`${BACKEND_URL}/${selectedJob.processed_video_path}`}
                        controls
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <div className="text-center p-4">
                        <span className="text-2xl block mb-2 font-emoji">⚙️</span>
                        <span className="text-slate-400 text-sm">Processed video will resolve once completed.</span>
                      </div>
                    )}
                  </div>

                  {/* Processing Status Panel */}
                  {(selectedJob.status === "processing" || selectedJob.status === "pending") && (
                    <div className="bg-navy-light/40 border border-navy-accent/35 rounded-xl p-4 space-y-3">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-300 flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-brand-cyan animate-pulse" />
                          Stage: {selectedJob.status === "pending" ? "Job Enqueued" : "Inference Frame Processing"}
                        </span>
                        <span className="font-mono text-brand-cyan">{selectedJob.progress}%</span>
                      </div>
                      <div className="w-full bg-navy-accent/15 rounded-full h-2 overflow-hidden">
                        <div className="bg-brand-cyan h-full transition-all duration-300" style={{ width: `${selectedJob.progress}%` }} />
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center text-xs pt-1">
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase block font-semibold">Processed</span>
                          <span className="text-slate-300 font-mono">{selectedJob.processed_frames} / {selectedJob.total_frames}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase block font-semibold">Speed FPS</span>
                          <span className="text-slate-300 font-mono">{selectedJob.processing_fps}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase block font-semibold">Vehicles</span>
                          <span className="text-slate-300 font-mono">{selectedJob.vehicles_detected}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase block font-semibold">Violations</span>
                          <span className="text-slate-300 font-mono text-status-red">{selectedJob.violations_detected}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Frame step controls */}
                  <div className="flex flex-wrap items-center justify-between gap-3 text-xs border-t border-navy-accent/20 pt-4">
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleStep("backward")}>◀ Step Back</Button>
                      <Button variant="outline" size="sm" onClick={() => handleStep("forward")}>Step Forward ▶</Button>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-500">Speed:</span>
                      {[0.5, 1.0, 1.5, 2.0].map(sp => (
                        <button
                          key={sp}
                          onClick={() => {
                            setPlaybackSpeed(sp);
                            if (originalVideoRef.current) originalVideoRef.current.playbackRate = sp;
                            if (processedVideoRef.current) processedVideoRef.current.playbackRate = sp;
                          }}
                          className={`px-2 py-1 rounded font-mono font-bold ${
                            playbackSpeed === sp ? "bg-brand-cyan text-navy-darker" : "bg-navy-light text-slate-400 hover:text-slate-200"
                          }`}
                        >
                          {sp}x
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-[280px] border border-dashed border-navy-accent/30 rounded-xl flex flex-col items-center justify-center p-6 text-center">
                  <span className="text-4xl mb-3">🎥</span>
                  <h4 className="text-slate-300 text-sm font-semibold">No Video Analysis Job Selected</h4>
                  <p className="text-xs text-slate-500 mt-2 max-w-sm">Select an active job from the history list below or drag-and-drop a new video to inspect results.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* TIMELINE, STATS & EVIDENCE GALLERY */}
      {selectedJobResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline */}
          <Card className="lg:col-span-1">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>4. Violations Timeline</CardTitle>
              <Button variant="outline" size="sm" className="text-xs" onClick={handleDownloadReport}>
                📄 Export CSV
              </Button>
            </CardHeader>
            <CardContent>
              {selectedJobResult.timeline && selectedJobResult.timeline.length > 0 ? (
                <div className="space-y-3.5 max-h-[360px] overflow-y-auto pr-2">
                  {selectedJobResult.timeline.map((event: TimelineEvent, idx: number) => (
                    <div
                      key={idx}
                      onClick={() => handleSeek(event.timestamp_sec)}
                      className="p-3 bg-navy-light/45 hover:bg-navy-accent/35 rounded-lg border border-navy-accent/30 flex items-center justify-between gap-3 cursor-pointer group transition-colors"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-status-red/10 border border-status-red/35 text-status-red font-bold uppercase">
                            {event.type.replace("_", " ")}
                          </span>
                          <span className="font-mono text-xs text-slate-100 group-hover:text-brand-cyan transition-colors">{event.plate}</span>
                        </div>
                        <p className="text-[10px] text-slate-500">Confidence: {(event.confidence * 100).toFixed(0)}%</p>
                      </div>
                      <span className="font-mono text-brand-cyan font-bold text-xs bg-navy-dark px-2 py-1 rounded">
                        ⏱️ {event.timestamp_str}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-slate-500">No violations flagged in this video clip.</div>
              )}
            </CardContent>
          </Card>

          {/* Stats & Evidence */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>5. Video Analytics Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                  <div className="bg-navy-light/35 p-3 rounded-lg border border-navy-accent/30">
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold">Total Vehicles</span>
                    <span className="text-2xl font-bold text-slate-200 font-mono mt-1 block">{selectedJobResult.vehicles_detected}</span>
                  </div>
                  <div className="bg-navy-light/35 p-3 rounded-lg border border-navy-accent/30">
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold">Total Violations</span>
                    <span className="text-2xl font-bold text-status-red font-mono mt-1 block">{selectedJobResult.violations_detected}</span>
                  </div>
                  <div className="bg-navy-light/35 p-3 rounded-lg border border-navy-accent/30">
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold">Average FPS</span>
                    <span className="text-2xl font-bold text-brand-cyan font-mono mt-1 block">{selectedJob?.processing_fps || 24.5}</span>
                  </div>
                  <div className="bg-navy-light/35 p-3 rounded-lg border border-navy-accent/30">
                    <span className="text-[10px] text-slate-500 uppercase block font-semibold">Processing Time</span>
                    <span className="text-2xl font-bold text-slate-200 font-mono mt-1 block">{selectedJob?.processing_time || 0}s</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>6. Evidence Crops Gallery</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedJobResult.evidence && selectedJobResult.evidence.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-[300px] overflow-y-auto pr-2">
                    {selectedJobResult.evidence.map((ev: EvidenceItem, idx: number) => (
                      <div key={idx} className="bg-navy-light/45 border border-navy-accent/30 p-3 rounded-lg flex gap-3 text-xs">
                        <div className="w-20 aspect-square rounded bg-black overflow-hidden border border-navy-accent/20 shrink-0 relative flex items-center justify-center">
                          {ev.plate_crop_path ? (
                            <img src={`${BACKEND_URL}/${ev.plate_crop_path}`} alt="License Plate Crop" className="w-full h-full object-contain" />
                          ) : (
                            <span className="text-slate-500 text-[10px]">No Crop</span>
                          )}
                        </div>
                        <div className="flex-1 space-y-1 min-w-0">
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-slate-200 truncate">{ev.verified_plate}</span>
                            <span className="text-[10px] text-brand-cyan font-mono">ID: #{ev.violation_id}</span>
                          </div>
                          <p className="text-slate-400 capitalize text-[10px]">{ev.violation_type.replace("_", " ")}</p>
                          <p className="text-slate-500 text-[9px]">Frame: {ev.frame_id} | Conf: {(ev.confidence * 100).toFixed(0)}%</p>
                          <div className="pt-2">
                            <a
                              href={`${BACKEND_URL}/${ev.annotated_frame_path}`}
                              target="_blank"
                              rel="noreferrer"
                              className="text-brand-cyan hover:underline text-[10px] font-semibold"
                            >
                              🔍 View Snap
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-8 text-center text-xs text-slate-500">No evidence snapshots generated.</div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* JOBS HISTORY LIST */}
      <Card>
        <CardHeader>
          <CardTitle>Analysis History Locker</CardTitle>
        </CardHeader>
        <CardContent>
          {jobs.length > 0 ? (
            <div className="border border-navy-accent/40 rounded-xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-navy-light border-b border-navy-accent/40 text-slate-400 font-semibold uppercase tracking-wider">
                      <th className="p-3.5">Job ID</th>
                      <th className="p-3.5">File Name</th>
                      <th className="p-3.5">Created At</th>
                      <th className="p-3.5">Violations</th>
                      <th className="p-3.5">Status</th>
                      <th className="p-3.5">Processing FPS</th>
                      <th className="p-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-navy-accent/20">
                    {jobs.map((j) => (
                      <tr key={j.id} className="hover:bg-navy-light/20 transition-colors text-slate-300">
                        <td className="p-3.5 font-mono text-brand-cyan">#{j.id}</td>
                        <td className="p-3.5 font-semibold truncate max-w-[180px]">{j.filename}</td>
                        <td className="p-3.5 text-slate-400">{new Date(j.created_at).toLocaleString()}</td>
                        <td className="p-3.5 font-mono text-status-red">{j.violations_detected}</td>
                        <td className="p-3.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            j.status === "completed" ? "bg-emerald-600/10 border border-emerald-500/20 text-emerald-400" :
                            j.status === "processing" ? "bg-brand-blue/15 border border-brand-cyan/25 text-brand-cyan animate-pulse" :
                            j.status === "failed" ? "bg-rose-600/10 border border-rose-500/20 text-rose-400" :
                            "bg-slate-700 text-slate-300"
                          }`}>
                            {j.status.toUpperCase()}
                          </span>
                        </td>
                        <td className="p-3.5 font-mono text-slate-400">{j.processing_fps}</td>
                        <td className="p-3.5 text-right flex justify-end gap-2.5">
                          <button
                            onClick={() => handleOpenJob(j)}
                            className="text-brand-cyan hover:underline font-semibold"
                          >
                            Open
                          </button>
                          <button
                            onClick={() => handleDeleteJob(j.id)}
                            className="text-status-red hover:underline font-semibold"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center gap-3 bg-navy-dark/10 border border-dashed border-navy-accent/25 rounded-xl text-center">
              <span className="text-3xl font-emoji">📭</span>
              <span className="text-slate-400 text-sm">No analysis history logged.</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

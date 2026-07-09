import React, { useState } from "react";
import { Button } from "../ui/Button";

interface SettingsData {
  smtp: {
    host: string;
    port: number;
    email: string;
    password?: string;
    use_tls: boolean;
    sender: string;
  };
  ai: {
    confidence_threshold: number;
    speed_limit_kmh: number;
    enabled_modules: string[];
  };
  upload_dir: string;
}

interface ConfigSettingsProps {
  settings: SettingsData;
  onSave: (data: SettingsData) => Promise<void>;
}

export function ConfigSettingsForm({ settings, onSave }: ConfigSettingsProps) {
  const [host, setHost] = useState(settings.smtp.host);
  const [port, setPort] = useState(settings.smtp.port);
  const [email, setEmail] = useState(settings.smtp.email);
  const [password, setPassword] = useState(settings.smtp.password || "");
  const [useTls, setUseTls] = useState(settings.smtp.use_tls);
  const [sender, setSender] = useState(settings.smtp.sender);
  const [confThreshold, setConfThreshold] = useState(settings.ai.confidence_threshold);
  const [speedLimit, setSpeedLimit] = useState(settings.ai.speed_limit_kmh);
  const [uploadDir, setUploadDir] = useState(settings.upload_dir);
  const [enabledModules, setEnabledModules] = useState<string[]>(settings.ai.enabled_modules);
  const [saving, setSaving] = useState(false);

  const availableModules = [
    "vehicle_detection",
    "vehicle_tracking",
    "helmet_detection",
    "seat_belt_detection",
    "phone_detection",
    "traffic_signal_detection",
    "wrong_side_detection",
    "triple_riding_detection",
    "number_plate_detection",
    "ocr"
  ];

  const handleModuleToggle = (moduleName: string) => {
    setEnabledModules((prev) =>
      prev.includes(moduleName)
        ? prev.filter((m) => m !== moduleName)
        : [...prev, moduleName]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({
        smtp: { host, port: Number(port), email, password, use_tls: useTls, sender },
        ai: { confidence_threshold: Number(confThreshold), speed_limit_kmh: Number(speedLimit), enabled_modules: enabledModules },
        upload_dir: uploadDir
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* SMTP Email Settings */}
      <div className="bg-navy-light rounded-lg border border-navy-accent/50 p-6">
        <h3 className="font-bold text-slate-100 text-base mb-4 flex items-center gap-2">
          <span>📧</span> SMTP Email Server Configurations
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">SMTP Host</label>
            <input
              type="text"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">SMTP Port</label>
            <input
              type="number"
              value={port}
              onChange={(e) => setPort(Number(e.target.value))}
              className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">SMTP Server Username/Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">SMTP Server App Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              placeholder="••••••••••••••••"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Default Email Sender Header</label>
            <input
              type="text"
              value={sender}
              onChange={(e) => setSender(e.target.value)}
              className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              required
            />
          </div>
          <div className="flex items-center mt-6">
            <label className="relative flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={useTls}
                onChange={(e) => setUseTls(e.target.checked)}
                className="w-4 h-4 bg-navy-dark border-navy-accent rounded accent-brand-cyan"
              />
              <span className="text-sm font-semibold text-slate-300">Use Secure TLS Connection</span>
            </label>
          </div>
        </div>
      </div>

      {/* AI & Speed Threshold Configs */}
      <div className="bg-navy-light rounded-lg border border-navy-accent/50 p-6">
        <h3 className="font-bold text-slate-100 text-base mb-4 flex items-center gap-2">
          <span>🧠</span> AI Inference Settings & Pipeline Modules
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">
              YOLO Confidence Threshold: <span className="font-mono text-brand-cyan">{confThreshold}</span>
            </label>
            <input
              type="range"
              min="0.1"
              max="0.9"
              step="0.05"
              value={confThreshold}
              onChange={(e) => setConfThreshold(Number(e.target.value))}
              className="w-full h-1.5 bg-navy-accent rounded-lg appearance-none cursor-pointer accent-brand-cyan"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1.5 font-mono">
              <span>0.1 (More False Positives)</span>
              <span>0.9 (Strict Detections)</span>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Speed Limit Violation Threshold (KM/H)</label>
            <input
              type="number"
              value={speedLimit}
              onChange={(e) => setSpeedLimit(Number(e.target.value))}
              className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
              required
            />
          </div>
        </div>

        {/* AI Pipeline Modules Checkbox Grid */}
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase mb-3">Active Pipeline Pipeline Modules</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {availableModules.map((mod) => {
              const isEnabled = enabledModules.includes(mod);
              return (
                <button
                  key={mod}
                  type="button"
                  onClick={() => handleModuleToggle(mod)}
                  className={`flex items-center justify-between p-3 rounded-lg border text-sm font-medium transition-all duration-200 text-left cursor-pointer ${
                    isEnabled
                      ? "bg-brand-blue/10 border-brand-blue/35 text-brand-cyan shadow-sm shadow-brand-blue/5"
                      : "bg-navy-dark border-navy-accent/50 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <span className="capitalize">{mod.replace(/_/g, " ")}</span>
                  <span className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center ${isEnabled ? "border-brand-cyan bg-brand-cyan" : "border-slate-600"}`}>
                    {isEnabled && <span className="w-1.5 h-1.5 rounded-full bg-navy-darker" />}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Storage and Directories */}
      <div className="bg-navy-light rounded-lg border border-navy-accent/50 p-6">
        <h3 className="font-bold text-slate-100 text-base mb-4 flex items-center gap-2">
          <span>💾</span> System Storage Directories
        </h3>
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase mb-2">Evidence Upload Storage Directory</label>
          <input
            type="text"
            value={uploadDir}
            onChange={(e) => setUploadDir(e.target.value)}
            className="w-full bg-navy-dark border border-navy-accent/50 text-slate-200 text-sm rounded-lg p-2.5 focus:outline-none focus:border-brand-cyan/50"
            required
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3.5">
        <Button variant="outline" type="button" onClick={() => window.location.reload()}>
          Cancel Changes
        </Button>
        <Button variant="primary" type="submit" disabled={saving}>
          {saving ? "Saving Configuration..." : "Save System Settings"}
        </Button>
      </div>
    </form>
  );
}

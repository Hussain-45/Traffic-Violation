import React, { useState, useEffect, useContext } from "react";
import { AuthContext, ThemeContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import {
  User,
  ShieldCheck,
  Eye,
  Globe,
  Sun,
  Moon,
  Cpu,
  Camera,
  Settings as SettingsIcon,
  Save,
  Lock,
  CameraOff
} from "lucide-react";

interface AIThresholds {
  ai_mode: string
  confidence_threshold: number
  speed_limit: number
}

interface CameraSetting {
  id: string
  name: string
  resolution: "1080p" | "720p" | "480p"
  fps_limit: number
}

export default function SystemSettings() {
  const { token, user, login } = useContext(AuthContext);
  const { theme, toggleTheme } = useContext(ThemeContext);

  // Form states: Profile
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [profileMsg, setProfileMsg] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  // Form states: Password
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);

  // Form states: Language & Theme
  const [language, setLanguage] = useState(localStorage.getItem("language") || "en");

  // Form states: AI Tuning
  const [aiMode, setAiMode] = useState("simulated");
  const [confThreshold, setConfThreshold] = useState(0.45);
  const [speedLimit, setSpeedLimit] = useState(60);
  const [aiMsg, setAiMsg] = useState("");
  const [savingAI, setSavingAI] = useState(false);

  // Camera stream settings (Stored locally for demo)
  const [cameras, setCameras] = useState<CameraSetting[]>([
    { id: "CAM-001", name: "Connaught Place Jn 1", resolution: "1080p", fps_limit: 30 },
    { id: "CAM-002", name: "India Gate Circular 3", resolution: "1080p", fps_limit: 30 },
    { id: "CAM-003", name: "Rajouri Garden Flyover", resolution: "720p", fps_limit: 25 },
    { id: "CAM-004", name: "AIIMS Crossing Main Feed", resolution: "720p", fps_limit: 15 },
    { id: "CAM-005", name: "Karol Bagh Bazar CCTV 3", resolution: "480p", fps_limit: 15 }
  ]);

  const syncProfileState = () => {
    if (user) {
      setFullName(user.full_name);
      setEmail(user.email || "");
    }
  };

  const fetchThresholds = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/settings/thresholds`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAiMode(data.ai_mode);
        setConfThreshold(data.confidence_threshold);
        setSpeedLimit(data.speed_limit);
      }
    } catch (err) {
      console.warn("Using offline AI thresholds configuration.");
    }
  };

  useEffect(() => {
    syncProfileState();
    fetchThresholds();
  }, [token, user]);

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileMsg("");

    try {
      const res = await fetch(`${API_BASE_URL}/users/me/profile`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ full_name: fullName, email })
      });

      if (res.ok) {
        const updatedUser = await res.json();
        setProfileMsg("Profile updated successfully!");
        if (user) {
          login(token!, { ...user, full_name: updatedUser.full_name, email: updatedUser.email });
        }
      } else {
        const err = await res.json();
        setProfileMsg(err.detail || "Profile update failed.");
      }
    } catch (err) {
      setProfileMsg("Profile updated (Simulation mode).");
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPassword(true);
    setPasswordMsg("");

    try {
      const res = await fetch(`${API_BASE_URL}/users/me/password`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
      });

      if (res.ok) {
        setPasswordMsg("Password updated successfully!");
        setCurrentPassword("");
        setNewPassword("");
      } else {
        const err = await res.json();
        setPasswordMsg(err.detail || "Password change rejected.");
      }
    } catch (err) {
      setPasswordMsg("Password update failed (Authentication error).");
    } finally {
      setSavingPassword(false);
    }
  };

  const handleLanguageSave = (val: string) => {
    setLanguage(val);
    localStorage.setItem("language", val);
    alert(`Language preference set to: ${val.toUpperCase()}`);
  };

  const handleAISave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingAI(true);
    setAiMsg("");

    try {
      const res = await fetch(`${API_BASE_URL}/settings/thresholds`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          ai_mode: aiMode,
          confidence_threshold: parseFloat(confThreshold as any),
          speed_limit: parseFloat(speedLimit as any)
        })
      });

      if (res.ok) {
        setAiMsg("AI tuning parameters updated successfully!");
      }
    } catch (err) {
      setAiMsg("AI parameters updated (Simulation Mode).");
    } finally {
      setSavingAI(false);
    }
  };

  const handleCameraResolutionChange = (id: string, resolution: "1080p" | "720p" | "480p") => {
    setCameras((prev) =>
      prev.map((c) => (c.id === id ? { ...c, resolution } : c))
    );
  };

  const handleCameraFpsChange = (id: string, fps_limit: number) => {
    setCameras((prev) =>
      prev.map((c) => (c.id === id ? { ...c, fps_limit } : c))
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">System Settings</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
          Configure appearances, language preferences, profile details, and AI thresholds.
        </p>
      </div>

      <Tabs defaultValue="profile" className="w-full">
        <TabsList className="grid w-full grid-cols-4 mb-6">
          <TabsTrigger value="profile" className="text-xs font-bold py-2">Profile & Credentials</TabsTrigger>
          <TabsTrigger value="appearance" className="text-xs font-bold py-2">Appearance & Locale</TabsTrigger>
          <TabsTrigger value="ai" className="text-xs font-bold py-2">AI Model Tuning</TabsTrigger>
          <TabsTrigger value="cameras" className="text-xs font-bold py-2">Camera Configurations</TabsTrigger>
        </TabsList>

        {/* Tab 1: Profile & Credentials */}
        <TabsContent value="profile" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Edit Profile */}
            <Card className="glass-card p-5 space-y-4">
              <CardHeader className="p-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <User size={15} className="text-blue-500" />
                  Officer Profile Details
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Update your contact email and identity display names.
                </CardDescription>
              </CardHeader>

              {profileMsg && (
                <div className="p-3 text-[10px] rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-500 font-bold">
                  {profileMsg}
                </div>
              )}

              <form onSubmit={handleProfileSave} className="space-y-4 text-xs font-semibold">
                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-450 uppercase">Full Identity Name</label>
                  <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required className="h-9 text-xs" />
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-450 uppercase">Email Address</label>
                  <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="h-9 text-xs" />
                </div>

                <Button type="submit" disabled={savingProfile} className="w-full h-9 text-[10px] font-bold">
                  {savingProfile ? "Saving Profile..." : "Save Profile"}
                </Button>
              </form>
            </Card>

            {/* Change Password */}
            <Card className="glass-card p-5 space-y-4">
              <CardHeader className="p-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Lock size={15} className="text-red-500" />
                  Credential Credentials Password
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Securely update your account access codes.
                </CardDescription>
              </CardHeader>

              {passwordMsg && (
                <div className="p-3 text-[10px] rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-500 font-bold">
                  {passwordMsg}
                </div>
              )}

              <form onSubmit={handlePasswordSave} className="space-y-4 text-xs font-semibold">
                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-450 uppercase">Current Password</label>
                  <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required className="h-9 text-xs" />
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-455 uppercase">New Password</label>
                  <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required className="h-9 text-xs" />
                </div>

                <Button type="submit" disabled={savingPassword} className="w-full h-9 text-[10px] font-bold">
                  {savingPassword ? "Updating Password..." : "Change Password"}
                </Button>
              </form>
            </Card>

          </div>
        </TabsContent>

        {/* Tab 2: Appearance & Locale */}
        <TabsContent value="appearance" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Theme Toggle */}
            <Card className="glass-card p-5 space-y-4">
              <CardHeader className="p-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  {theme === "dark" ? <Moon size={15} className="text-amber-500" /> : <Sun size={15} className="text-amber-500" />}
                  Theme Configuration
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Select your preferred desktop visual display theme.
                </CardDescription>
              </CardHeader>

              <div className="flex gap-4">
                <Button
                  onClick={() => theme !== "light" && toggleTheme()}
                  variant={theme === "light" ? "default" : "outline"}
                  className="flex-1 text-[10px] font-bold h-9"
                >
                  <Sun size={14} className="mr-1.5" /> Light Mode
                </Button>
                <Button
                  onClick={() => theme !== "dark" && toggleTheme()}
                  variant={theme === "dark" ? "default" : "outline"}
                  className="flex-1 text-[10px] font-bold h-9"
                >
                  <Moon size={14} className="mr-1.5" /> Dark Mode
                </Button>
              </div>
            </Card>

            {/* Language Preference */}
            <Card className="glass-card p-5 space-y-4">
              <CardHeader className="p-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Globe size={15} className="text-blue-500" />
                  Language & Locale
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Adjust default dashboard language overlays.
                </CardDescription>
              </CardHeader>

              <div className="space-y-3">
                <Select value={language} onChange={(e) => handleLanguageSave(e.target.value)} className="h-9">
                  <option value="en">English (Official Interface)</option>
                  <option value="hi">Hindi (हिन्दी)</option>
                  <option value="es">Spanish (Español)</option>
                  <option value="fr">French (Français)</option>
                </Select>
              </div>
            </Card>

          </div>
        </TabsContent>

        {/* Tab 3: AI Model Tuning */}
        <TabsContent value="ai" className="space-y-6">
          <div className="max-w-xl mx-auto">
            <Card className="glass-card p-6 space-y-5">
              <CardHeader className="p-0">
                <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Cpu size={16} className="text-blue-500" />
                  AI Threshold & Pipeline Tuning
                </CardTitle>
                <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                  Manage active YOLOv8 image processing parameters and speed limits.
                </CardDescription>
              </CardHeader>

              {aiMsg && (
                <div className="p-3 text-[10px] rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-500 font-bold">
                  {aiMsg}
                </div>
              )}

              <form onSubmit={handleAISave} className="space-y-4 text-xs font-semibold">
                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-450 uppercase">Execution Mode</label>
                  <Select value={aiMode} onChange={(e) => setAiMode(e.target.value)} className="h-9">
                    <option value="active">Active Inference Mode (Real YOLOv8/EasyOCR)</option>
                    <option value="simulated">Simulation Mode (High-Fidelity Telemetry Graphics)</option>
                  </Select>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-[9px] font-bold uppercase tracking-wider">
                    <span className="text-slate-400">AI Confidence Threshold</span>
                    <span className="text-blue-500">{Math.round(confThreshold * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.10"
                    max="0.95"
                    step="0.05"
                    value={confThreshold}
                    onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                    className="w-full accent-blue-500 bg-slate-200 dark:bg-slate-800 h-1 rounded-lg cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-450 uppercase">Junction Speed Limit (KM/H)</label>
                  <Input type="number" value={speedLimit} onChange={(e) => setSpeedLimit(parseInt(e.target.value))} className="h-9 text-xs" />
                </div>

                <Button type="submit" disabled={savingAI} className="w-full h-9 text-[10px] font-bold">
                  {savingAI ? "Saving Tuning..." : "Save AI Parameters"}
                </Button>
              </form>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 4: Camera Configurations */}
        <TabsContent value="cameras" className="space-y-6">
          <Card className="glass-card p-5 space-y-4">
            <CardHeader className="p-0">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Camera size={15} className="text-blue-500" />
                CCTV Node Resolution & FPS Mapping
              </CardTitle>
              <CardDescription className="text-[10px] text-slate-500 mt-0.5">
                Optimize camera resolutions and stream frame rates to balance bandwidth.
              </CardDescription>
            </CardHeader>

            <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-2xl">
              <table className="w-full text-xs font-semibold text-left">
                <thead className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 text-[10px] font-bold uppercase tracking-wider text-slate-450">
                  <tr>
                    <th className="p-3">Camera Node</th>
                    <th className="p-3">Stream Quality</th>
                    <th className="p-3">Framerate Limit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-250/20">
                  {cameras.map((c) => (
                    <tr key={c.id}>
                      <td className="p-3">
                        <strong className="text-slate-800 dark:text-slate-100">{c.name}</strong>
                        <span className="text-[9px] text-slate-450 block uppercase font-bold">{c.id}</span>
                      </td>
                      <td className="p-3">
                        <Select
                          value={c.resolution}
                          onChange={(e) => handleCameraResolutionChange(c.id, e.target.value as any)}
                          className="h-8 w-28 text-[10px]"
                        >
                          <option value="1080p">1080p (Full HD)</option>
                          <option value="720p">720p (Standard HD)</option>
                          <option value="480p">480p (Low Bandwidth)</option>
                        </Select>
                      </td>
                      <td className="p-3">
                        <Select
                          value={c.fps_limit}
                          onChange={(e) => handleCameraFpsChange(c.id, parseInt(e.target.value))}
                          className="h-8 w-28 text-[10px]"
                        >
                          <option value={30}>30 FPS</option>
                          <option value={25}>25 FPS</option>
                          <option value={15}>15 FPS</option>
                          <option value={10}>10 FPS</option>
                        </Select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

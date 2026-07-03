import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "../components/ui/table";
import { Settings, Cpu, IndianRupee, Save, ShieldCheck } from "lucide-react";

interface FineRule {
  violation_type: string
  amount: number
  description: string
}

interface AIThresholds {
  ai_mode: string
  confidence_threshold: number
  speed_limit: number
}

// Fallback mock fine rules
const fallbackFines: FineRule[] = [
  { violation_type: "red_light_jump", amount: 2000, description: "Jumping red traffic signal lights" },
  { violation_type: "wrong_lane", amount: 1000, description: "Driving in dedicated bus/wrong lanes" },
  { violation_type: "overspeeding", amount: 1000, description: "Exceeding speed limits" },
  { violation_type: "no_helmet", amount: 500, description: "Riding two-wheeler without helmet" },
  { violation_type: "no_seatbelt", amount: 500, description: "Driving car without seatbelt" }
];

export default function SystemSettings() {
  const { token, user } = useContext(AuthContext);

  const [fines, setFines] = useState<FineRule[]>([]);
  const [thresholds, setThresholds] = useState<AIThresholds | null>(null);

  const [loadingFines, setLoadingFines] = useState<boolean>(true);
  const [loadingThresholds, setLoadingThresholds] = useState<boolean>(true);

  // Form states
  const [aiMode, setAiMode] = useState("active");
  const [confThreshold, setConfThreshold] = useState(0.45);
  const [speedLimit, setSpeedLimit] = useState(60.0);

  const [updatingThresholds, setUpdatingThresholds] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [editingFineType, setEditingFineType] = useState<string | null>(null);
  const [editFineVal, setEditFineVal] = useState("");

  const fetchFines = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/settings/fines`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setFines(data);
      } else {
        throw new Error("API Offline");
      }
    } catch (err) {
      console.warn("Using offline fine rule directory.");
      setFines(fallbackFines);
    } finally {
      setLoadingFines(false);
    }
  };

  const fetchThresholds = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/settings/thresholds`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setThresholds(data);
        setAiMode(data.ai_mode);
        setConfThreshold(data.confidence_threshold);
        setSpeedLimit(data.speed_limit);
      } else {
        throw new Error("API Offline");
      }
    } catch (err) {
      console.warn("Using offline AI thresholds parameters.");
      setThresholds({ ai_mode: "simulated", confidence_threshold: 0.45, speed_limit: 60 });
    } finally {
      setLoadingThresholds(false);
    }
  };

  useEffect(() => {
    fetchFines();
    fetchThresholds();
  }, [token]);

  const handleThresholdSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (user?.role !== "admin") return;

    setUpdatingThresholds(true);
    setSuccessMsg("");
    try {
      const res = await fetch(`${API_BASE_URL}/settings/thresholds`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ai_mode: aiMode,
          confidence_threshold: parseFloat(confThreshold as any),
          speed_limit: parseFloat(speedLimit as any),
        }),
      });

      if (res.ok) {
        setSuccessMsg("AI parameters updated successfully!");
        fetchThresholds();
      }
    } catch (err) {
      console.warn("API Offline. Updating parameters locally.");
      setSuccessMsg("AI parameters saved (Simulation Mode).");
    } finally {
      setUpdatingThresholds(false);
    }
  };

  const handleFineEditClick = (rule: FineRule) => {
    if (user?.role !== "admin") return;
    setEditingFineType(rule.violation_type);
    setEditFineVal(rule.amount.toString());
  };

  const handleFineSaveSubmit = async (violationType: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/settings/fines/${violationType}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ amount: parseFloat(editFineVal) }),
      });
      if (res.ok) {
        setEditingFineType(null);
        fetchFines();
      }
    } catch (err) {
      console.warn("API Offline. Modifying fine tariff locally.");
      setFines((prev) =>
        prev.map((f) =>
          f.violation_type === violationType ? { ...f, amount: parseFloat(editFineVal) } : f
        )
      );
      setEditingFineType(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">System Settings</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Modify active AI detection mode, confidence sliders, and fine tariff directories.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Fine Rules Tariff (Left spanned) */}
        <div className="xl:col-span-2">
          <Card className="glass-card p-6 space-y-4">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <IndianRupee size={16} className="text-blue-500" />
              Challan Tariff Registry
            </CardTitle>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Offence Code</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Fine Tariff</TableHead>
                  {user?.role === "admin" && <th className="pb-3 text-center">Action</th>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadingFines ? (
                  [1, 2].map((i) => (
                    <TableRow key={i} className="animate-pulse">
                      <TableCell><div className="h-4 w-24 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                      <TableCell><div className="h-4 w-48 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                      <TableCell><div className="h-4 w-12 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                      <TableCell><div className="h-7 w-12 rounded bg-slate-200 dark:bg-slate-800 mx-auto"></div></TableCell>
                    </TableRow>
                  ))
                ) : (
                  fines.map((rule) => (
                    <TableRow key={rule.violation_type}>
                      <TableCell className="font-bold text-slate-700 dark:text-slate-200 uppercase">
                        {rule.violation_type.replace("_", " ")}
                      </TableCell>
                      <TableCell className="text-slate-500 font-semibold">{rule.description}</TableCell>
                      <TableCell className="font-extrabold text-slate-850 dark:text-slate-100">
                        {editingFineType === rule.violation_type ? (
                          <Input
                            type="number"
                            value={editFineVal}
                            onChange={(e) => setEditFineVal(e.target.value)}
                            className="w-20 h-8 text-xs p-1 bg-slate-100 dark:bg-slate-900 border border-slate-250 dark:border-slate-800 rounded text-white"
                          />
                        ) : (
                          `₹${rule.amount}`
                        )}
                      </TableCell>
                      {user?.role === "admin" && (
                        <TableCell className="text-center">
                          {editingFineType === rule.violation_type ? (
                            <Button
                              onClick={() => handleFineSaveSubmit(rule.violation_type)}
                              size="sm"
                              className="h-8 text-[10px] px-2.5 bg-emerald-500 hover:bg-emerald-600 shadow-sm"
                            >
                              Save
                            </Button>
                          ) : (
                            <Button
                              onClick={() => handleFineEditClick(rule)}
                              variant="outline"
                              size="sm"
                              className="h-8 text-[10px] px-2.5 text-blue-500 hover:bg-blue-600 hover:text-white"
                            >
                              Edit
                            </Button>
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </div>

        {/* AI Thresholds (Right Column) */}
        <div>
          <Card className="glass-card p-6 space-y-4 shadow-sm">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Cpu size={16} className="text-blue-500" />
              AI Model Tuning desk
            </CardTitle>

            {successMsg && (
              <div className="flex items-center gap-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 p-3 text-[10px] text-emerald-500 font-bold">
                <ShieldCheck size={14} />
                <span>{successMsg}</span>
              </div>
            )}

            {loadingThresholds ? (
              <div className="h-40 rounded bg-slate-200 dark:bg-slate-800 animate-pulse"></div>
            ) : (
              <form onSubmit={handleThresholdSave} className="space-y-4 text-xs font-semibold">
                
                <div className="space-y-1">
                  <label className="text-slate-400 block uppercase tracking-wider text-[9px] font-bold">
                    AI Execution Mode
                  </label>
                  <Select
                    disabled={user?.role !== "admin"}
                    value={aiMode}
                    onChange={(e) => setAiMode(e.target.value)}
                  >
                    <option value="active">Active Inference Mode (Real YOLOv8/EasyOCR)</option>
                    <option value="simulated">Simulation Mode (High-Fidelity Telemetry Graphics)</option>
                  </Select>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between font-bold uppercase tracking-wider text-[9px]">
                    <span className="text-slate-400">Confidence Threshold</span>
                    <span className="text-blue-500">{Math.round(confThreshold * 100)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.10"
                    max="0.95"
                    step="0.05"
                    disabled={user?.role !== "admin"}
                    value={confThreshold}
                    onChange={(e) => setConfThreshold(parseFloat(e.target.value))}
                    className="w-full accent-blue-500 bg-slate-200 dark:bg-slate-800 h-1 rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-slate-400 block uppercase tracking-wider text-[9px] font-bold">
                    System Speed Limit (KM/H)
                  </label>
                  <Input
                    type="number"
                    disabled={user?.role !== "admin"}
                    value={speedLimit}
                    onChange={(e) => setSpeedLimit(parseFloat(e.target.value))}
                    className="h-10 text-xs text-white"
                  />
                </div>

                {user?.role === "admin" && (
                  <Button
                    type="submit"
                    disabled={updatingThresholds}
                    className="w-full py-3 text-xs flex items-center justify-center gap-1.5 shadow-md"
                  >
                    <Save size={12} />
                    Save Parameters
                  </Button>
                )}

              </form>
            )}
          </Card>
        </div>

      </div>
    </div>
  );
}

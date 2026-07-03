import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "../components/ui/table";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import {
  FileText,
  Download,
  Calendar,
  Layers,
  Clock,
  Printer,
  Trash2,
  FileSpreadsheet,
  AlertCircle,
  TrendingUp,
  CheckCircle,
  Search
} from "lucide-react";

interface ReportLog {
  id: number
  title: string
  generated_by: number
  report_type: string
  start_date: string
  end_date: string
  file_path: string
  created_at: string
}

export default function Reports() {
  const { token } = useContext(AuthContext);

  // Form states
  const [reportTitle, setReportTitle] = useState("");
  const [duration, setDuration] = useState("weekly"); // daily, weekly, monthly, yearly
  const [reportType, setReportType] = useState("violations"); // violations, revenue, analytics
  const [fileFormat, setFileFormat] = useState("xlsx"); // csv, xlsx, pdf
  
  // History logs
  const [reports, setReports] = useState<ReportLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Live preview metrics (mock values reflecting selected range)
  const [previewStats, setPreviewStats] = useState({
    violationsCount: 142,
    fineSum: 168000,
    cameraUptime: 98.4,
    accuracy: 94.6
  });

  const [previewChartData, setPreviewChartData] = useState([
    { name: "Mon", count: 18, fines: 18000 },
    { name: "Tue", count: 24, fines: 26000 },
    { name: "Wed", count: 15, fines: 15000 },
    { name: "Thu", count: 22, fines: 22000 },
    { name: "Fri", count: 31, fines: 35000 },
    { name: "Sat", count: 20, fines: 40000 },
    { name: "Sun", count: 12, fines: 12000 }
  ]);

  const fetchReportsList = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/reports`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }
    } catch (err) {
      console.warn("Using offline mock reports history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportsList();
  }, [token]);

  // Adjust preview stats when duration switches
  useEffect(() => {
    if (duration === "daily") {
      setPreviewStats({ violationsCount: 22, fineSum: 24000, cameraUptime: 99.1, accuracy: 95.2 });
      setPreviewChartData([
        { name: "08:00", count: 3, fines: 3000 },
        { name: "12:00", count: 7, fines: 8000 },
        { name: "16:00", count: 9, fines: 10000 },
        { name: "20:00", count: 3, fines: 3000 }
      ]);
    } else if (duration === "weekly") {
      setPreviewStats({ violationsCount: 142, fineSum: 168000, cameraUptime: 98.4, accuracy: 94.6 });
      setPreviewChartData([
        { name: "Mon", count: 18, fines: 18000 },
        { name: "Tue", count: 24, fines: 26000 },
        { name: "Wed", count: 15, fines: 15000 },
        { name: "Thu", count: 22, fines: 22000 },
        { name: "Fri", count: 31, fines: 35000 },
        { name: "Sat", count: 20, fines: 40000 },
        { name: "Sun", count: 12, fines: 12000 }
      ]);
    } else if (duration === "monthly") {
      setPreviewStats({ violationsCount: 620, fineSum: 742000, cameraUptime: 97.9, accuracy: 94.1 });
      setPreviewChartData([
        { name: "Week 1", count: 130, fines: 150000 },
        { name: "Week 2", count: 160, fines: 190000 },
        { name: "Week 3", count: 180, fines: 210000 },
        { name: "Week 4", count: 150, fines: 192000 }
      ]);
    } else {
      setPreviewStats({ violationsCount: 7840, fineSum: 9245000, cameraUptime: 98.1, accuracy: 94.4 });
      setPreviewChartData([
        { name: "Jan", count: 580, fines: 620000 },
        { name: "Feb", count: 620, fines: 740000 },
        { name: "Mar", count: 700, fines: 810000 },
        { name: "Apr", count: 680, fines: 790000 },
        { name: "May", count: 810, fines: 950000 },
        { name: "Jun", count: 910, fines: 1080000 }
      ]);
    }
  }, [duration]);

  const handleGenerateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportTitle) return;
    setSubmitting(true);

    // Calculate dates
    const end = new Date();
    const start = new Date();
    if (duration === "daily") start.setDate(end.getDate() - 1);
    else if (duration === "weekly") start.setDate(end.getDate() - 7);
    else if (duration === "monthly") start.setDate(end.getDate() - 30);
    else start.setFullYear(end.getFullYear() - 1);

    try {
      const res = await fetch(`${API_BASE_URL}/reports`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          title: reportTitle,
          report_type: reportType,
          start_date: start.toISOString(),
          end_date: end.toISOString(),
          file_format: fileFormat
        })
      });

      if (res.ok) {
        setReportTitle("");
        fetchReportsList();
      }
    } catch (err) {
      console.warn("API offline, mock appending generated report locally.");
      const mockLog: ReportLog = {
        id: Date.now(),
        title: reportTitle,
        generated_by: 1,
        report_type: reportType,
        start_date: start.toISOString(),
        end_date: end.toISOString(),
        file_path: `/data/reports/mock_${reportType}.${fileFormat}`,
        created_at: new Date().toISOString()
      };
      setReports((prev) => [mockLog, ...prev]);
      setReportTitle("");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteReport = async (id: number) => {
    try {
      const res = await fetch(`${API_BASE_URL}/reports/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setReports((prev) => prev.filter((r) => r.id !== id));
      }
    } catch (err) {
      setReports((prev) => prev.filter((r) => r.id !== id));
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Reporting Command</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
            Compile automated logs, download Excel spreadsheets, or print diagnostic PDFs.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left Side: Report Request Form */}
        <div className="xl:col-span-1 print:hidden">
          <Card className="glass-card p-5 space-y-4">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers size={14} className="text-blue-500" />
              Compile Report File
            </CardTitle>

            <form onSubmit={handleGenerateReport} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-450 uppercase">Report Title</label>
                <Input
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  placeholder="e.g. June Weekly Violations Summary"
                  required
                  className="h-9 text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-450 uppercase">Time Duration</label>
                  <Select value={duration} onChange={(e) => setDuration(e.target.value)} className="h-9">
                    <option value="daily">Daily (Past 24h)</option>
                    <option value="weekly">Weekly (Past 7d)</option>
                    <option value="monthly">Monthly (Past 30d)</option>
                    <option value="yearly">Yearly (Past 365d)</option>
                  </Select>
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] font-bold text-slate-450 uppercase">Report Type</label>
                  <Select value={reportType} onChange={(e) => setReportType(e.target.value)} className="h-9">
                    <option value="violations">Violations List</option>
                    <option value="revenue">Revenue & Payments</option>
                    <option value="analytics">System Diagnostics</option>
                  </Select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] font-bold text-slate-450 uppercase">File Format</label>
                <Select value={fileFormat} onChange={(e) => setFileFormat(e.target.value)} className="h-9">
                  <option value="xlsx">Excel Sheet (.xlsx)</option>
                  <option value="csv">CSV Data file (.csv)</option>
                  <option value="pdf">Diagnostic PDF (.pdf)</option>
                </Select>
              </div>

              <Button type="submit" disabled={submitting} className="w-full h-9 text-[10px] font-bold mt-2">
                {submitting ? "Compiling..." : "Generate and Save"}
              </Button>
            </form>
          </Card>
        </div>

        {/* Right Side: Live Report Preview & Print page */}
        <div className="xl:col-span-2 space-y-6 print:col-span-3 print:space-y-8">
          
          <Card className="glass-card p-6 space-y-5 border-slate-200/50 dark:border-slate-800/60 shadow-lg relative print:bg-white print:text-black print:border-none print:shadow-none">
            
            {/* Delhi police letterhead header shown on print */}
            <div className="hidden print:flex items-center justify-between border-b-2 border-black pb-4 mb-4">
              <div>
                <h2 className="text-lg font-black uppercase tracking-wider">Delhi Enforcement Division</h2>
                <span className="text-[10px] font-bold text-slate-600 block uppercase">Gov-AI Smart Traffic Control Bureau</span>
              </div>
              <div className="text-right text-[9px] font-semibold text-slate-600">
                <span>Date generated: {new Date().toLocaleDateString()}</span>
                <span className="block">Report status: Official Audit Record</span>
              </div>
            </div>

            {/* Print trigger on screen preview */}
            <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-850/40 pb-3 print:hidden">
              <div>
                <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">Live preview desk</span>
                <CardTitle className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                  {reportTitle || `${duration.toUpperCase()} ${reportType.toUpperCase()} PREVIEW`}
                </CardTitle>
              </div>
              <Button onClick={handlePrint} variant="outline" size="sm" className="h-8 text-[10px] font-bold">
                <Printer size={12} className="mr-1.5" /> Print Preview (PDF)
              </Button>
            </div>

            {/* Statistics Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-semibold print:text-black">
              <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-900/60 border border-slate-200/40 dark:border-slate-800/40 print:bg-slate-100 print:border-slate-300">
                <span className="text-[8px] font-bold uppercase tracking-wider text-slate-400 block">Total Offences</span>
                <strong className="text-base font-black text-slate-800 dark:text-slate-100 print:text-black">{previewStats.violationsCount}</strong>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-900/60 border border-slate-200/40 dark:border-slate-800/40 print:bg-slate-100 print:border-slate-300">
                <span className="text-[8px] font-bold uppercase tracking-wider text-slate-400 block">Fines Value</span>
                <strong className="text-base font-black text-slate-800 dark:text-slate-100 print:text-black">₹{previewStats.fineSum.toLocaleString()}</strong>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-900/60 border border-slate-200/40 dark:border-slate-800/40 print:bg-slate-100 print:border-slate-300">
                <span className="text-[8px] font-bold uppercase tracking-wider text-slate-400 block">CCTV Uptime</span>
                <strong className="text-base font-black text-slate-800 dark:text-slate-100 print:text-black">{previewStats.cameraUptime}%</strong>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-900/60 border border-slate-200/40 dark:border-slate-800/40 print:bg-slate-100 print:border-slate-300">
                <span className="text-[8px] font-bold uppercase tracking-wider text-slate-400 block">AI Accuracy</span>
                <strong className="text-base font-black text-slate-800 dark:text-slate-100 print:text-black">{previewStats.accuracy}%</strong>
              </div>
            </div>

            {/* Charts Preview */}
            <div className="h-48 print:h-32">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={previewChartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" className="hidden dark:block print:hidden" />
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" className="dark:hidden print:block" />
                  <XAxis dataKey="name" tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                  <YAxis tickLine={false} axisLine={false} style={{ fontSize: '9px', fontWeight: 'bold' }} />
                  <Tooltip contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', color: '#fff', fontSize: '9px' }} />
                  <Bar dataKey={reportType === "revenue" ? "fines" : "count"} fill="#3b82f6" radius={[3, 3, 0, 0]} name={reportType === "revenue" ? "Fines (₹)" : "Violations"} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Official Footer signature space on print */}
            <div className="hidden print:flex justify-between items-end pt-12 text-[10px] font-bold">
              <div>
                <span className="block border-t border-black w-40 text-center">Delhi Police Officer</span>
                <span className="text-slate-500 text-[8px] block text-center">Signature Stamp</span>
              </div>
              <div className="text-right text-[8px] text-slate-400">
                <span>System UID check code: STVDS-PDF-LOG-882</span>
              </div>
            </div>
          </Card>

          {/* Report History Grid */}
          <Card className="glass-card p-5 space-y-4 print:hidden">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Clock size={16} className="text-blue-500" />
              Generated Report History Logs
            </CardTitle>

            <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-2xl">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Report Name</TableHead>
                    <TableHead>Duration Type</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-slate-450 font-bold py-6 animate-pulse">
                        Loading reports log history...
                      </TableCell>
                    </TableRow>
                  ) : reports.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-slate-450 font-bold py-6">
                        No reports generated yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    reports.map((rep) => (
                      <TableRow key={rep.id}>
                        <TableCell className="font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5 mt-2">
                          <FileText size={14} className="text-blue-400" />
                          {rep.title}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="text-[8px] font-bold uppercase px-1.5 py-0">
                            {rep.report_type}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-450 text-[10px]">
                          {new Date(rep.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right space-x-1.5">
                          <Button
                            onClick={() => window.open(`${API_BASE_URL.replace("/api/v1", "")}${rep.file_path}`, "_blank")}
                            variant="ghost"
                            size="sm"
                            className="h-7 text-blue-500 bg-blue-500/5 hover:bg-blue-600 hover:text-white px-2.5 text-[9px] font-bold"
                          >
                            <Download size={10} className="mr-1" /> Download
                          </Button>
                          <Button
                            onClick={() => handleDeleteReport(rep.id)}
                            variant="ghost"
                            size="sm"
                            className="h-7 text-red-500 bg-red-500/5 hover:bg-red-600 hover:text-white px-2 text-[9px] font-bold"
                          >
                            <Trash2 size={10} />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}

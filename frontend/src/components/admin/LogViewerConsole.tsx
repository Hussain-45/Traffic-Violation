import React from "react";
import { Button } from "../ui/Button";

interface LogViewerProps {
  logsData: {
    log_file: string;
    total_lines: number;
    lines: string[];
  };
  onRefresh: () => Promise<void>;
}

export function LogViewerConsole({ logsData, onRefresh }: LogViewerProps) {
  const getLogLineStyle = (line: string) => {
    if (line.includes("[ERROR]") || line.includes("failed") || line.includes("HTTP Exception") || line.includes("CRITICAL")) {
      return "text-status-red bg-status-red/5 font-semibold";
    }
    if (line.includes("[WARNING]") || line.includes("warning") || line.includes("WARNING")) {
      return "text-amber-400 bg-amber-500/5";
    }
    if (line.includes("[INFO]") || line.includes("HTTP GET") || line.includes("HTTP POST")) {
      return "text-slate-300";
    }
    return "text-slate-400";
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs text-slate-400">Viewing active logs for file: </span>
          <span className="text-xs font-mono text-brand-cyan bg-navy-accent/50 px-2 py-1 rounded ml-1 border border-navy-accent/50">
            {logsData.log_file}
          </span>
        </div>
        <Button variant="outline" size="sm" onClick={onRefresh}>
          🔄 Refresh Logs
        </Button>
      </div>

      {/* Terminal Output Console Box */}
      <div className="h-[450px] w-full rounded-lg bg-[#030509] border border-navy-accent/60 p-4 font-mono text-xs overflow-y-auto space-y-1.5 shadow-inner">
        {logsData.lines.length > 0 ? (
          logsData.lines.map((line, idx) => (
            <div
              key={idx}
              className={`p-1.5 rounded transition-colors duration-150 hover:bg-navy-light/10 ${getLogLineStyle(line)}`}
            >
              <span className="text-[10px] text-slate-500 mr-2.5 select-none">{String(idx + 1).padStart(3, "0")}</span>
              <span>{line}</span>
            </div>
          ))
        ) : (
          <div className="h-full flex items-center justify-center text-slate-600 uppercase tracking-widest text-xs select-none">
            No system log lines found.
          </div>
        )}
      </div>
    </div>
  );
}

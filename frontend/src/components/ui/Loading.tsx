import React from "react";

interface LoadingProps {
  fullPage?: boolean;
  size?: "sm" | "md" | "lg";
  text?: string;
}

export function Loading({ fullPage = false, size = "md", text = "Loading..." }: LoadingProps) {
  const sizeClasses = {
    sm: "w-5 h-5 border-2",
    md: "w-8 h-8 border-3",
    lg: "w-12 h-12 border-4",
  };

  const containerStyle = fullPage
    ? "fixed inset-0 bg-navy-darker/90 z-50 flex flex-col items-center justify-center gap-4"
    : "flex flex-col items-center justify-center p-8 gap-3 w-full h-full min-h-[200px]";

  return (
    <div className={containerStyle}>
      <div
        className={`animate-spin rounded-full border-t-brand-cyan border-r-transparent border-b-transparent border-l-transparent ${sizeClasses[size]}`}
        style={{ borderColor: "var(--color-navy-accent)" }}
      ></div>
      {text && (
        <span className="text-xs font-medium tracking-wider text-slate-400 uppercase select-none animate-pulse">
          {text}
        </span>
      )}
    </div>
  );
}

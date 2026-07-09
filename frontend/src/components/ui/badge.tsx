import React from "react";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "info" | "success" | "warning" | "danger" | "neutral";
  children: React.ReactNode;
}

export function Badge({ variant = "neutral", children, className = "", ...props }: BadgeProps) {
  const baseStyle =
    "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold select-none border";

  const variants = {
    neutral: "bg-navy-accent/50 text-slate-300 border-navy-accent",
    info: "bg-brand-blue/10 text-brand-blue border-brand-blue/20",
    success: "bg-status-green/10 text-status-green border-status-green/20",
    warning: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    danger: "bg-status-red/10 text-status-red border-status-red/20",
  };

  return (
    <span className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>
      {children}
    </span>
  );
}

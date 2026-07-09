import React from "react";

interface SectionHeaderProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
  className?: string;
}

export function SectionHeader({ title, description, children, className = "" }: SectionHeaderProps) {
  return (
    <div className={`flex items-center justify-between gap-4 mb-4 ${className}`}>
      <div>
        <h2 className="text-lg font-semibold text-slate-200 tracking-tight">{title}</h2>
        {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
      </div>
      {children && <div className="flex items-center gap-2 shrink-0">{children}</div>}
    </div>
  );
}

import React from "react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

export function EmptyState({ title, description, icon, children }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center rounded-xl border border-dashed border-navy-accent/50 bg-navy-light/20 max-w-md mx-auto">
      {icon ? (
        <div className="p-4 bg-navy-accent/40 rounded-full border border-navy-accent/30 text-slate-400 mb-4">
          {icon}
        </div>
      ) : (
        <div className="w-12 h-12 rounded-full border border-dashed border-navy-accent flex items-center justify-center text-slate-500 mb-4">
          ❓
        </div>
      )}
      <h4 className="text-base font-semibold text-slate-200">{title}</h4>
      <p className="text-xs text-slate-400 mt-2 max-w-xs leading-relaxed">{description}</p>
      {children && <div className="mt-6">{children}</div>}
    </div>
  );
}

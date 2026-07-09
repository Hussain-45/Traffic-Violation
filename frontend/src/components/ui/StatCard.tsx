import React from "react";
import { Card, CardContent } from "./Card";

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  description?: string;
  className?: string;
}

export function StatCard({ title, value, icon, description, className = "" }: StatCardProps) {
  return (
    <Card className={`overflow-hidden ${className}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
            <h4 className="text-2xl font-bold text-slate-100 mt-2">{value}</h4>
          </div>
          {icon && (
            <div className="p-3 bg-navy-accent/40 rounded-lg border border-navy-accent/20 text-brand-cyan">
              {icon}
            </div>
          )}
        </div>
        {description && (
          <p className="text-xs text-slate-400 mt-3 flex items-center gap-1.5">
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

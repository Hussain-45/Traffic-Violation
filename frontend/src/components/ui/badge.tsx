import * as React from "react"
import { cn } from "../../lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider transition-colors focus:outline-none",
        {
          "border-transparent bg-blue-600 text-white shadow shadow-blue-500/10": variant === "default",
          "border-transparent bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100": variant === "secondary",
          "border-transparent bg-red-500/10 text-red-500 border-red-500/20": variant === "destructive",
          "border-transparent bg-emerald-500/10 text-emerald-500 border-emerald-500/20": variant === "success",
          "border-slate-200 text-slate-900 dark:border-slate-800 dark:text-slate-100": variant === "outline"
        },
        className
      )}
      {...props}
    />
  )
}

export { Badge }

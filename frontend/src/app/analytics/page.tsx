"use client";

import React from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";

export default function AnalyticsPage() {
  return (
    <div>
      <PageHeader
        title="Metrics & Charts"
        description="Visualize hourly traffic flow counts, violation distribution matrices, and intersection performance stats."
      />
      
      <div className="py-12">
        <EmptyState
          title="Interactive Analytics Coming Soon"
          description="We are setting up the charting layouts to render time-series metrics dynamically from database history."
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-8 h-8 text-brand-cyan"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0 0 20.25 18V6A2.25 2.25 0 0 0 18 3.75H6A2.25 2.25 0 0 0 3.75 6v12A2.25 2.25 0 0 0 6 20.25Z"
              />
            </svg>
          }
        />
      </div>
    </div>
  );
}

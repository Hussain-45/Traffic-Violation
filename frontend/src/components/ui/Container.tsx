import React from "react";

interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  fluid?: boolean;
}

export function Container({ children, fluid = false, className = "", ...props }: ContainerProps) {
  return (
    <div
      className={`${fluid ? "w-full" : "max-w-7xl"} mx-auto px-4 sm:px-6 lg:px-8 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

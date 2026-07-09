"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "./Button";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error inside React tree:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = "/";
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="fixed inset-0 z-50 bg-navy-darker flex flex-col items-center justify-center p-6 text-center">
          <div className="w-16 h-16 rounded-full bg-status-red/10 border border-status-red/30 flex items-center justify-center text-status-red text-2xl mb-6 animate-pulse">
            ⚠️
          </div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Something went wrong</h2>
          <p className="text-xs text-slate-400 max-w-sm mt-3 leading-relaxed">
            The Traffic Violation AI dashboard encountered a critical client-side layout crash.
          </p>
          {this.state.error && (
            <pre className="mt-4 p-4 rounded-lg bg-navy-light text-left text-xs font-mono text-status-red border border-navy-accent/40 max-w-lg overflow-auto max-h-40">
              {this.state.error.toString()}
            </pre>
          )}
          <div className="flex gap-4 mt-6">
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              Reload Page
            </Button>
            <Button variant="primary" size="sm" onClick={this.handleReset}>
              Go to Home
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
export default ErrorBoundary;

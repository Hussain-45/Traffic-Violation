import type { Metadata } from "next";
import "./globals.css";
import { AppProvider } from "@/lib/api";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { Shell } from "@/components/layout/Shell";

export const metadata: Metadata = {
  title: "Traffic Violation AI",
  description: "AI-powered Smart Traffic Violation Detection System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="h-full bg-navy-darker">
        <ErrorBoundary>
          <AppProvider>
            <Shell>{children}</Shell>
          </AppProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}

import React, { createContext, useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import LiveMonitoring from "./pages/LiveMonitoring";
import Upload from "./pages/Upload";
import Violations from "./pages/Violations";
import Analytics from "./pages/Analytics";
import Map from "./pages/Map";
import Cameras from "./pages/Cameras";
import Users from "./pages/Users";
import Settings from "./pages/Settings";
import Reports from "./pages/Reports";
import FineManagement from "./pages/FineManagement";

// TypeScript Interfaces for Global Contexts
export interface UserProfile {
  id?: number
  username: string
  full_name: string
  role: "admin" | "officer"
  email?: string
}

interface AuthContextType {
  token: string | null
  user: UserProfile | null
  loading: boolean
  login: (token: string, user: UserProfile) => void
  logout: () => void
}

interface ThemeContextType {
  theme: "dark" | "light"
  toggleTheme: () => void
}

export const AuthContext = createContext<AuthContextType>({} as AuthContextType);
export const ThemeContext = createContext<ThemeContextType>({} as ThemeContextType);

export const API_BASE_URL = "http://localhost:8000/api/v1";
export const FILE_SERVER_URL = "http://localhost:8000";

// Protected Route Guard
const ProtectedRoute = ({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) => {
  const { token, user, loading } = React.useContext(AuthContext);
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-900 text-white">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Main Dashboard Layout
const DashboardLayout = ({ children }: { children: React.ReactNode }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 transition-colors duration-300 dark:bg-slate-950 dark:text-white">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? "md:ml-64" : "md:ml-20"}`}>
        <Topbar />
        <main className="flex-1 p-4 md:p-6 overflow-y-auto h-[calc(100vh-4rem)]">
          {children}
        </main>
      </div>
    </div>
  );
};

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem("token") || null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [theme, setTheme] = useState<"dark" | "light">((localStorage.getItem("theme") as "dark" | "light") || "dark");

  // Sync class theme settings
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  // Sync profile details if token exists
  useEffect(() => {
    const syncProfile = async () => {
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }
      try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          // Token expired, clear session
          handleLogout();
        }
      } catch (err) {
        console.warn("API offline, booting in Stand-alone Demo Mode.");
        // Fallback demo user for stand-alone frontend testing
        setUser({
          username: "admin",
          full_name: "Super Admin (Demo)",
          role: "admin",
          email: "admin@smarttraffic.gov.in"
        });
      } finally {
        setLoading(false);
      }
    };
    syncProfile();
  }, [token]);

  const handleLogin = (newToken: string, userDetails: UserProfile) => {
    localStorage.setItem("token", newToken);
    setToken(newToken);
    setUser(userDetails);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  return (
    <AuthContext.Provider value={{ token, user, loading, login: handleLogin, logout: handleLogout }}>
      <ThemeContext.Provider value={{ theme, toggleTheme }}>
        <Router>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<Login />} />

            {/* Private Routing */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Dashboard />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/live"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <LiveMonitoring />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/upload"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Upload />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/violations"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Violations />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Analytics />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/map"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Map />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/cameras"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Cameras />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute allowedRoles={["admin"]}>
                  <DashboardLayout>
                    <Users />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Settings />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <Reports />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/fines"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <FineManagement />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </ThemeContext.Provider>
    </AuthContext.Provider>
  );
}

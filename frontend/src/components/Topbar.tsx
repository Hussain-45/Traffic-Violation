import React, { useContext, useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthContext, ThemeContext, API_BASE_URL } from "../App";
import { Bell, Sun, Moon, Search, User as UserIcon, LogOut, CheckCircle, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function Topbar() {
  const { token, user, logout } = useContext(AuthContext);
  const { theme, toggleTheme } = useContext(ThemeContext);
  const location = useLocation();
  const navigate = useNavigate();

  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<any[]>([]);

  // Translate paths to breadcrumb names
  const pageNames: { [key: string]: string } = {
    "/dashboard": "Dashboard Hub",
    "/live": "Live Video Feeds",
    "/upload": "AI Media Upload",
    "/violations": "Violations Database",
    "/analytics": "Intelligence Analytics",
    "/map": "Hotspot Grid Map",
    "/cameras": "CCTV Checkpoints",
    "/users": "Officer Controls",
    "/settings": "System Mappings",
    "/notifications": "Alerts History"
  };

  const currentPath = location.pathname;
  const pageTitle = pageNames[currentPath] || "Smart Command Center";

  const handleLogoutClick = () => {
    logout();
    navigate("/login");
  };

  const fetchNotifs = async () => {
    if (!token) return;
    try {
      const resCount = await fetch(`${API_BASE_URL}/notifications/unread-count`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (resCount.ok) {
        const d = await resCount.json();
        setUnreadCount(d.count);
      }

      const resList = await fetch(`${API_BASE_URL}/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (resList.ok) {
        const list = await resList.json();
        setNotifications(list.slice(0, 5));
      }
    } catch (e) {
      console.warn("Offline fallback alerts mapping.");
    }
  };

  useEffect(() => {
    fetchNotifs();
    const timer = setInterval(fetchNotifs, 12000);
    return () => clearInterval(timer);
  }, [token]);

  const handleDismissAll = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/notifications/read-all`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setUnreadCount(0);
        setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      }
    } catch (e) {
      setUnreadCount(0);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/50 bg-white/75 px-4 md:px-8 backdrop-blur-md dark:border-slate-800/50 dark:bg-slate-950/80 transition-colors duration-300">
      
      {/* Page Title / Breadcrumb */}
      <div className="flex items-center">
        <h2 className="text-sm font-bold tracking-tight text-slate-800 dark:text-white uppercase">
          {pageTitle}
        </h2>
      </div>

      {/* Global Actions */}
      <div className="flex items-center gap-4">
        
        {/* Search Input (Desktop) */}
        <div className="relative hidden md:block w-60">
          <Search size={14} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search system logs..."
            className="w-full rounded-xl bg-slate-100/60 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 p-2 pl-9 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-semibold"
          />
        </div>

        {/* Theme Switcher (Quick Toggle) */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-500 dark:text-slate-400 transition-colors"
        >
          {theme === "dark" ? <Sun size={18} className="text-amber-500" /> : <Moon size={18} />}
        </button>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => { setNotifOpen(!notifOpen); setProfileOpen(false); }}
            className="relative p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-500 dark:text-slate-400 transition-colors cursor-pointer"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 h-4 w-4 rounded-full bg-red-500 text-white text-[8px] flex items-center justify-center font-bold">
                {unreadCount}
              </span>
            )}
          </button>
          
          <AnimatePresence>
            {notifOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute right-0 mt-2 w-80 rounded-2xl border border-slate-200/50 bg-white/95 dark:border-slate-800/50 dark:bg-slate-950/95 shadow-xl backdrop-blur-md p-3 space-y-3 z-50 text-xs text-slate-800 dark:text-slate-100"
              >
                <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-800/40 pb-2">
                  <span className="font-bold uppercase tracking-wider text-[10px] text-slate-450">Active Alerts</span>
                  {unreadCount > 0 && (
                    <button
                      onClick={handleDismissAll}
                      className="text-[9px] text-blue-500 hover:text-blue-450 font-bold uppercase cursor-pointer"
                    >
                      Dismiss all
                    </button>
                  )}
                </div>
                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="text-center py-6 text-slate-450 font-bold">
                      No active notifications.
                    </div>
                  ) : (
                    notifications.map((n) => (
                      <div
                        key={n.id}
                        className={`p-2.5 rounded-xl flex gap-2 border transition-all ${
                          n.is_read
                            ? "bg-slate-50/50 border-transparent dark:bg-slate-900/30 text-slate-500"
                            : "bg-blue-500/5 border-blue-500/10 dark:bg-blue-600/10 dark:border-blue-500/20"
                        }`}
                      >
                        {n.type === "fine" ? (
                          <AlertTriangle size={14} className="text-red-500 shrink-0 mt-0.5" />
                        ) : n.type === "camera" ? (
                          <AlertTriangle size={14} className="text-amber-500 shrink-0 mt-0.5" />
                        ) : (
                          <CheckCircle size={14} className="text-blue-450 shrink-0 mt-0.5" />
                        )}
                        <div>
                          <strong className="block text-[10px] font-bold">{n.title}</strong>
                          <p className="text-[9.5px] leading-normal font-semibold mt-0.5">{n.message}</p>
                          <span className="text-[8px] text-slate-400 font-bold block mt-1">
                            {new Date(n.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                <div className="border-t border-slate-200/40 dark:border-slate-850/40 pt-2 text-center">
                  <button
                    onClick={() => { setNotifOpen(false); navigate("/notifications"); }}
                    className="text-[9px] text-blue-500 font-extrabold uppercase hover:underline cursor-pointer"
                  >
                    View Alerts History
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* User Account Controls */}
        <div className="relative">
          <button
            onClick={() => { setProfileOpen(!profileOpen); setNotifOpen(false); }}
            className="flex items-center justify-center h-8 w-8 rounded-xl bg-blue-100 text-blue-700 font-bold dark:bg-slate-900 dark:text-slate-300 border border-slate-200/50 dark:border-slate-800/50 cursor-pointer"
          >
            {user ? user.full_name.charAt(0) : "O"}
          </button>

          <AnimatePresence>
            {profileOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute right-0 mt-2 w-56 rounded-2xl border border-slate-200/50 bg-white/95 dark:border-slate-800/50 dark:bg-slate-950/95 shadow-xl backdrop-blur-md p-4 z-50 text-xs space-y-4"
              >
                {user && (
                  <div className="space-y-1">
                    <strong className="block text-slate-800 dark:text-white font-bold">{user.full_name}</strong>
                    <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold block">{user.role}</span>
                    <span className="text-[10px] text-slate-500 font-semibold block">{user.email || `${user.username}@traffic.gov.in`}</span>
                  </div>
                )}
                
                <button
                  onClick={handleLogoutClick}
                  className="w-full flex items-center justify-between p-2 rounded-xl text-red-500 hover:bg-red-500/10 transition-colors font-bold"
                >
                  <span>Sign Out</span>
                  <LogOut size={16} />
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

      </div>
    </header>
  );
}

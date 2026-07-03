import React, { useContext, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthContext, ThemeContext } from "../App";
import { Bell, Sun, Moon, Search, User as UserIcon, LogOut, CheckCircle, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function Topbar() {
  const { user, logout } = useContext(AuthContext);
  const { theme, toggleTheme } = useContext(ThemeContext);
  const location = useLocation();
  const navigate = useNavigate();

  const [notifOpen, setNotifOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

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
  };

  const currentPath = location.pathname;
  const pageTitle = pageNames[currentPath] || "Smart Command Center";

  const handleLogoutClick = () => {
    logout();
    navigate("/login");
  };

  const mockNotifs = [
    { id: 1, text: "Red Light Jump by DL 3C AB 9081 at Connaught Place", time: "2 min ago", type: "error" },
    { id: 2, text: "Overspeeding by MH 12 PQ 5510 at Rajpath (78 km/h)", time: "10 min ago", type: "warning" },
  ];

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
            className="relative p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-500 dark:text-slate-400 transition-colors"
          >
            <Bell size={18} />
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
          </button>
          
          <AnimatePresence>
            {notifOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute right-0 mt-2 w-72 rounded-2xl border border-slate-200/50 bg-white/95 dark:border-slate-800/50 dark:bg-slate-950/95 shadow-xl backdrop-blur-md p-3 space-y-3 z-50 text-xs"
              >
                <div className="flex justify-between items-center border-b border-slate-200/40 dark:border-slate-800/40 pb-2">
                  <span className="font-bold">System Alerts</span>
                  <span className="text-[10px] text-blue-500 font-bold uppercase cursor-pointer">Dismiss all</span>
                </div>
                <div className="space-y-2">
                  {mockNotifs.map((n) => (
                    <div key={n.id} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 flex gap-2">
                      {n.type === "error" ? (
                        <AlertTriangle size={14} className="text-red-500 shrink-0 mt-0.5" />
                      ) : (
                        <AlertTriangle size={14} className="text-amber-500 shrink-0 mt-0.5" />
                      )}
                      <div>
                        <p className="text-slate-700 dark:text-slate-300 font-semibold">{n.text}</p>
                        <span className="text-[9px] text-slate-400 font-bold block mt-1">{n.time}</span>
                      </div>
                    </div>
                  ))}
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

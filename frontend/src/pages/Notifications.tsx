import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import {
  Bell,
  AlertTriangle,
  CheckCircle,
  Clock,
  Search,
  Trash2,
  Check,
  Mail,
  Volume2
} from "lucide-react";

interface NotificationItem {
  id: number
  user_id: number | null
  title: string
  message: string
  type: "fine" | "camera" | "system" | "officer"
  is_read: boolean
  created_at: string
}

export default function Notifications() {
  const { token } = useContext(AuthContext);

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch (err) {
      console.warn("Using offline mock alerts history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [token]);

  const handleMarkAsRead = async (id: number) => {
    try {
      const res = await fetch(`${API_BASE_URL}/notifications/${id}/read`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
        );
      }
    } catch (err) {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/notifications/read-all`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      }
    } catch (err) {
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    }
  };

  // Filter alerts by search query and tabs
  const filteredNotifs = notifications.filter((n) => {
    const matchesSearch =
      n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      n.message.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesTab = filterType === "all" || n.type === filterType;
    return matchesSearch && matchesTab;
  });

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="space-y-6">
      
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Alerts Log Registry</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
            Track automated system notifications, fine dispatch statuses, and camera offline reports.
          </p>
        </div>

        {unreadCount > 0 && (
          <Button
            onClick={handleMarkAllAsRead}
            size="sm"
            className="text-[10px] font-bold h-9 bg-blue-600 hover:bg-blue-500 text-white shadow-md"
          >
            <Check size={12} className="mr-1.5" /> Mark All as Read
          </Button>
        )}
      </div>

      {/* Stats Quickbar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs font-semibold">
        <Card className="glass-card flex items-center gap-4 p-4">
          <div className="h-10 w-10 rounded-xl bg-red-500/10 text-red-500 flex items-center justify-center shrink-0">
            <Bell size={20} className="animate-pulse" />
          </div>
          <div>
            <span className="text-[10px] text-slate-450 font-bold uppercase tracking-widest block">Unread Alerts</span>
            <strong className="text-base font-black text-slate-800 dark:text-slate-100">{unreadCount} logs</strong>
          </div>
        </Card>

        <Card className="glass-card flex items-center gap-4 p-4">
          <div className="h-10 w-10 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0">
            <Mail size={20} />
          </div>
          <div>
            <span className="text-[10px] text-slate-455 font-bold uppercase tracking-widest block">Email Alerts Sent</span>
            <strong className="text-base font-black text-slate-800 dark:text-slate-100">
              {notifications.filter((n) => n.type === "fine").length} notifications
            </strong>
          </div>
        </Card>

        <Card className="glass-card flex items-center gap-4 p-4">
          <div className="h-10 w-10 rounded-xl bg-indigo-500/10 text-indigo-500 flex items-center justify-center shrink-0">
            <Volume2 size={20} />
          </div>
          <div>
            <span className="text-[10px] text-slate-455 font-bold uppercase tracking-widest block">System Diagnostics</span>
            <strong className="text-base font-black text-slate-800 dark:text-slate-100">
              {notifications.filter((n) => n.type === "camera" || n.type === "system").length} records
            </strong>
          </div>
        </Card>
      </div>

      {/* Main Filter & Search Console */}
      <Card className="glass-card p-4 space-y-4">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          
          <div className="relative w-full md:w-64">
            <Search size={14} className="absolute left-3 top-3 text-slate-400" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search alert body contents..."
              className="pl-9 text-xs h-9"
            />
          </div>

          <Tabs defaultValue="all" value={filterType} onValueChange={setFilterType} className="w-full md:w-auto">
            <TabsList className="grid grid-cols-5 text-[10px] font-bold h-9">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="fine">Fines</TabsTrigger>
              <TabsTrigger value="camera">Cameras</TabsTrigger>
              <TabsTrigger value="officer">Officer</TabsTrigger>
              <TabsTrigger value="system">System</TabsTrigger>
            </TabsList>
          </Tabs>

        </div>

        {/* Alerts Stack */}
        <div className="space-y-3.5 max-h-[480px] overflow-y-auto pr-1">
          {loading ? (
            <div className="text-center py-12 text-slate-450 font-bold animate-pulse">
              Syncing alert database feeds...
            </div>
          ) : filteredNotifs.length === 0 ? (
            <div className="text-center py-12 text-slate-450 font-bold border border-slate-200/50 dark:border-slate-800/40 rounded-2xl">
              No matching alerts logged.
            </div>
          ) : (
            filteredNotifs.map((item) => {
              const isUnread = !item.is_read;
              
              return (
                <div
                  key={item.id}
                  className={`p-4 rounded-2xl border transition-all duration-200 flex items-start justify-between gap-4 ${
                    isUnread
                      ? "border-blue-500/20 bg-blue-600/5 dark:bg-blue-600/10 shadow-sm"
                      : "border-slate-200 bg-white dark:border-slate-850/40 dark:bg-slate-950/60"
                  }`}
                >
                  <div className="flex gap-3 text-xs font-semibold">
                    <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                      item.type === "fine"
                        ? "bg-red-500/10 text-red-500 border border-red-500/20"
                        : item.type === "camera"
                        ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                        : "bg-blue-500/10 text-blue-500 border border-blue-500/20"
                    }`}>
                      {item.type === "fine" || item.type === "camera" ? (
                        <AlertTriangle size={15} />
                      ) : (
                        <CheckCircle size={15} />
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <strong className="text-slate-800 dark:text-slate-100">{item.title}</strong>
                        <Badge variant="outline" className="text-[7.5px] uppercase font-bold py-0">
                          {item.type}
                        </Badge>
                        {isUnread && (
                          <Badge className="bg-blue-500 text-white text-[7px] py-0">NEW</Badge>
                        )}
                      </div>
                      <p className="text-[10.5px] text-slate-500 dark:text-slate-400 font-semibold leading-relaxed">
                        {item.message}
                      </p>
                      <span className="text-[8px] text-slate-400 font-bold block flex items-center gap-1">
                        <Clock size={10} />
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {isUnread && (
                    <Button
                      onClick={() => handleMarkAsRead(item.id)}
                      variant="ghost"
                      size="sm"
                      className="h-7 text-blue-500 bg-blue-500/5 hover:bg-blue-600 hover:text-white px-2.5 text-[9px] font-bold"
                    >
                      Dismiss
                    </Button>
                  )}
                </div>
              );
            })
          )}
        </div>
      </Card>
    </div>
  );
}

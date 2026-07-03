import React, { useState, useEffect, useContext } from "react";
import { AuthContext, API_BASE_URL } from "../App";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "../components/ui/table";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Select } from "../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog";
import { Plus, Trash2, Clock } from "lucide-react";

interface UserItem {
  id: number
  username: string
  email: string
  full_name: string
  role: string
  status: string
}

interface AuditLogItem {
  id: number
  username: string
  action: string
  timestamp: string
}

const fallbackUsers: UserItem[] = [
  { id: 1, username: "admin", email: "admin@smarttraffic.gov.in", full_name: "Super Admin", role: "admin", status: "active" },
  { id: 2, username: "officer", email: "officer@smarttraffic.gov.in", full_name: "Officer Rajesh Kumar", role: "officer", status: "active" }
];

const fallbackLogs: AuditLogItem[] = [
  { id: 1, username: "admin", action: "System initialized and seeded mock historical dataset.", timestamp: new Date().toISOString() },
  { id: 2, username: "officer", action: "Updated violation status for incident #101.", timestamp: new Date().toISOString() }
];

export default function Users() {
  const { token, user: currentUser } = useContext(AuthContext);

  const [users, setUsers] = useState<UserItem[]>([]);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [logsLoading, setLogsLoading] = useState<boolean>(true);

  // Form states
  const [addModal, setAddModal] = useState<boolean>(false);
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("officer");
  const [formErr, setFormErr] = useState("");

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
      } else {
        throw new Error("API Offline");
      }
    } catch (err) {
      console.warn("Using offline users registry.");
      setUsers(fallbackUsers);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/users/logs`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      } else {
        throw new Error("API Offline");
      }
    } catch (err) {
      console.warn("Using offline system logs.");
      setLogs(fallbackLogs);
    } finally {
      setLogsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchLogs();
  }, [token]);

  const handleToggleStatusSubmit = async (user: UserItem) => {
    if (user.id === currentUser?.id) return;

    const newStatus = user.status === "active" ? "inactive" : "active";
    try {
      const res = await fetch(`${API_BASE_URL}/users/${user.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: newStatus, role: user.role }),
      });
      if (res.ok) {
        fetchUsers();
        fetchLogs();
      }
    } catch (err) {
      console.warn("API Offline. Toggling officer status locally.");
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, status: newStatus } : u))
      );
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErr("");

    if (!username || !fullName || !email || !password) {
      setFormErr("Please fill all required registration fields.");
      return;
    }

    const payload = { username, full_name: fullName, email, password, role };

    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        setAddModal(false);
        setUsername(""); setFullName(""); setEmail(""); setPassword(""); setRole("officer");
        fetchUsers();
        fetchLogs();
      } else {
        const errData = await res.json();
        setFormErr(errData.detail || "Registration failed.");
      }
    } catch (err) {
      console.warn("API Offline. Registering officer locally.");
      const mockNew: UserItem = {
        id: Math.floor(Math.random() * 100),
        username,
        email,
        full_name: fullName,
        role,
        status: "active"
      };
      setUsers((prev) => [...prev, mockNew]);
      setAddModal(false);
      setUsername(""); setFullName(""); setEmail(""); setPassword(""); setRole("officer");
    }
  };

  const handleDeleteUserSubmit = async (id: number, name: string) => {
    if (id === currentUser?.id) return;
    if (!window.confirm(`Delete officer account ${name}?`)) return;

    try {
      const res = await fetch(`${API_BASE_URL}/users/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        fetchUsers();
        fetchLogs();
      }
    } catch (err) {
      console.warn("API Offline. Deleting user locally.");
      setUsers((prev) => prev.filter((u) => u.id !== id));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-tight">Officer Administration</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Manage police officer accounts, update role permissions, and audit command center logs.
          </p>
        </div>
        <Button
          onClick={() => setAddModal(true)}
          className="text-xs font-bold py-2 h-9"
        >
          <Plus size={14} className="mr-1.5" />
          Register Officer
        </Button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Officers Grid List (Left spanned) */}
        <div className="xl:col-span-2">
          <Card className="glass-card shadow-sm overflow-hidden p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Officer Name</TableHead>
                  <TableHead>Username</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-center">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  [1, 2].map((i) => (
                    <TableRow key={i} className="animate-pulse">
                      <TableCell><div className="h-4 w-28 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                      <TableCell><div className="h-4 w-16 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                      <TableCell><div className="h-4 w-32 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                      <TableCell><div className="h-4 w-12 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                      <TableCell><div className="h-4 w-12 rounded bg-slate-200 dark:bg-slate-800"></div></TableCell>
                      <TableCell><div className="h-7 w-12 rounded bg-slate-200 dark:bg-slate-800 mx-auto"></div></TableCell>
                    </TableRow>
                  ))
                ) : (
                  users.map((u) => (
                    <TableRow key={u.id}>
                      <TableCell>
                        <div className="flex items-center gap-2.5">
                          <div className="h-7 w-7 rounded-full bg-slate-200 dark:bg-slate-800 text-[10px] flex items-center justify-center font-bold">
                            {u.full_name.charAt(0)}
                          </div>
                          <span>{u.full_name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-bold text-slate-500">{u.username}</TableCell>
                      <TableCell className="text-[10px] text-slate-500 font-semibold">{u.email}</TableCell>
                      <TableCell>
                        <Badge variant={u.role === "admin" ? "default" : "secondary"}>
                          {u.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={u.status === "active" ? "success" : "destructive"}>
                          {u.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex justify-center gap-1.5">
                          <Button
                            disabled={u.id === currentUser?.id}
                            onClick={() => handleToggleStatusSubmit(u)}
                            variant="outline"
                            size="sm"
                            className="h-8 text-[10px] px-2"
                          >
                            Toggle
                          </Button>
                          <Button
                            disabled={u.id === currentUser?.id}
                            onClick={() => handleDeleteUserSubmit(u.id, u.full_name)}
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-red-500 hover:bg-red-500/10"
                          >
                            <Trash2 size={12} />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </div>

        {/* Audit Logs Tickers (Right Column) */}
        <div>
          <Card className="glass-card p-5 space-y-4 shadow-sm">
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Clock size={16} className="text-blue-500" />
              Auditable Command Actions
            </CardTitle>

            <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
              {logsLoading ? (
                [1, 2].map((i) => (
                  <div key={i} className="h-10 rounded bg-slate-200 dark:bg-slate-800 animate-pulse"></div>
                ))
              ) : (
                logs.map((log) => (
                  <div key={log.id} className="text-[10px] border-b border-slate-100 dark:border-slate-900 pb-2 last:border-b-0 space-y-1">
                    <div className="flex justify-between font-bold text-slate-400">
                      <span className="text-blue-500 capitalize">{log.username}</span>
                      <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="font-semibold text-slate-600 dark:text-slate-350 leading-relaxed">
                      {log.action}
                    </p>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

      </div>

      {/* dialog modal */}
      <Dialog open={addModal} onOpenChange={setAddModal}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="text-sm font-bold text-white">Register Officer</DialogTitle>
            <DialogDescription className="text-[10px] text-slate-400">
              Provide credentials for the traffic police registry.
            </DialogDescription>
          </DialogHeader>

          {formErr && (
            <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-2.5 text-[10px] text-red-400 font-bold">
              {formErr}
            </div>
          )}

          <form onSubmit={handleRegisterSubmit} className="space-y-3 mt-2">
            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-400 uppercase">Full Name *</label>
              <Input type="text" required placeholder="Officer Ramesh Gupta" value={fullName} onChange={(e) => setFullName(e.target.value)} className="h-9 text-xs text-white" />
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-400 uppercase">Username *</label>
              <Input type="text" required placeholder="enforcer_103" value={username} onChange={(e) => setUsername(e.target.value)} className="h-9 text-xs text-white" />
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-400 uppercase">Email *</label>
              <Input type="email" required placeholder="officer@traffic.gov.in" value={email} onChange={(e) => setEmail(e.target.value)} className="h-9 text-xs text-white" />
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-400 uppercase">Password *</label>
              <Input type="password" required placeholder="Min 6 chars" value={password} onChange={(e) => setPassword(e.target.value)} className="h-9 text-xs text-white" />
            </div>

            <div className="space-y-1">
              <label className="text-[9px] font-bold text-slate-400 uppercase">Registry Role *</label>
              <Select value={role} onChange={(e) => setRole(e.target.value)} className="h-9 text-xs py-1">
                <option value="officer">Traffic Police Officer (Standard)</option>
                <option value="admin">Control Room Administrator (Admin)</option>
              </Select>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" size="sm" onClick={() => setAddModal(false)}>Cancel</Button>
              <Button type="submit" size="sm">Save Account</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
